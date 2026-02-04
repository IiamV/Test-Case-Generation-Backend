# LLM abstraction layer for interacting with a local Ollama server
from ollama import AsyncClient, ChatResponse
from app.core.config import settings
from typing import List, Optional
import httpx
import traceback
from app.models.ollama import OllamaChatResponse

# System prompt injected into the custom local Ollama model to constrain behavior
OLLAMA_SYSTEM_PROMPT = """
You are a test engineering assistant specialized in deriving system-level test cases from software requirements.
Your task is to analyze provided requirements and produce complete, unambiguous system test cases. Output MUST be valid JSON following the correct schema only with every field filled

For each step:
- input_data MUST contain the literal data values entered or used
- action MUST describe the user/system behavior WITHOUT embedding data
- input_data MUST NOT be null if data is required

Rules:
- Name of the fields in the JSON schema are all snake_case.
- Do NOT mismatch the name of fields of the JSON schema.
- Must fill every field of the JSON model.
- Do NOT ask for anything, this is a one time chat session.
- Generate ONLY test cases directly traceable to the provided requirements.
- DO NOT generate test cases about test cases, test suites, output format, or instructions.
- Do NOT include code, code snippets, function calls, or pseudo-code in any field.
- Use descriptive IDs like "TC-001". Use titles with spaces (no underscores).
- Actions must be human-executable instructions (e.g., "Enter 'user@example.com' into Email field and click Login").
- Use clear, deterministic language suitable for QA automation or manual execution.
- Generate only system-level (black-box) testcases derived from the requirements provided.
- Do not include implementation details or internal design assumptions.
- Do not explain your reasoning or include commentary.
- If a required field cannot be determined, set it to an empty array, null, or boolean false as appropriate — do not invent extra facts.
- Stop generation once all requirements are covered.
"""


# Shared async Ollama client configured via application settings
ollama_client = AsyncClient(
    host=settings.OLLAMA_HOST,
    headers={
        "Authorization": f"Bearer {settings.OLLAMA_API_KEY}"
    }
)


async def ollama_init() -> None:
    """
    Initializes the Ollama client by ensuring the required base, embedding, and custom models exist locally.

    If the OLLAMA_API_KEY is set, this function does nothing.

    Otherwise, it checks for the presence of the required models and pulls them from the Ollama cloud if they are missing.
    If the custom model does not exist, it is created with a fixed system prompt.

    Raises:
        RuntimeError: If the Ollama initialization fails for any reason.
    """

    if settings.OLLAMA_API_KEY is not None:
        return None

    # Initialize Ollama by ensuring required base and custom models exist locally
    llm_ok: bool = False      # Tracks presence of base LLM model
    embed_ok: bool = False    # Tracks presence of embedding model
    custom_ok: bool = False   # Tracks presence of derived custom model

    try:
        # Retrieve all locally available models from Ollama
        models = (await ollama_client.list()).models

        if models:
            for model in models:
                name = model.model
                if name == settings.LOCAL_LLM_MODEL:
                    llm_ok = True
                if name == settings.LOCAL_EMBED_MODEL:
                    embed_ok = True
                if name == settings.CUSTOM_LLM_MODEL:
                    custom_ok = True

                # Exit early once all required models are confirmed
                if llm_ok and embed_ok and custom_ok:
                    break

        # Pull missing base LLM model
        if not llm_ok:
            await ollama_client.pull(model=str(settings.LOCAL_LLM_MODEL))

        # Pull missing embedding model
        if not embed_ok:
            await ollama_client.pull(model=str(settings.LOCAL_EMBED_MODEL))

        # Create the custom model with a fixed system prompt if it does not exist
        if not custom_ok:
            await ollama_client.create(
                model=str(settings.CUSTOM_LLM_MODEL),
                from_=str(settings.LOCAL_LLM_MODEL),
                system=OLLAMA_SYSTEM_PROMPT
            )
    except Exception as e:
        # Log stack trace for diagnostics and propagate a domain-specific failure
        traceback.print_exc()
        raise RuntimeError(f"Ollama Initialization Failed: {e}")

    return None


async def get_ollama_model() -> str:
    """
    Resolve the LLM model name based on Ollama authentication configuration.

    If no Ollama API key is provided, the function returns the name of the local LLM model.
    Otherwise, it returns the name of the local LLM model.

    Returns:
        str: The name of the LLM model to use.
    """

    # Resolve the LLM model name based on Ollama authentication configuration
    if settings.OLLAMA_API_KEY is not None:
        return settings.LOCAL_LLM_MODEL

    return settings.CUSTOM_LLM_MODEL


async def ollama_healthcheck() -> None:
    """
    Check the health status of the OLLAMA server.
    This function will raise a RuntimeError if the OLLAMA server is not reachable.
    """

    # Perform a lightweight HTTP reachability check against the Ollama API
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{settings.OLLAMA_HOST}/api/tags")
        response.raise_for_status()


async def local_llm_chat(prompt: List[str], think: Optional[bool]) -> ChatResponse:
    """
    Interact with the local OLLAMA server to generate testcases from provided requirements.

    Args:
        prompt (List[str]): A list of strings representing the software requirements to be analyzed.
        think (Optional[bool]): A boolean indicating whether the LLM should generate a single function or a code block based on the requirements.

    Returns:
        ChatResponse: A structured response validated by the OllamaChatResponse schema containing the generated testcases.

    Raises:
        ValueError: If the local LLM returns no response.
    """

    # Send user requirements to the custom Ollama model and enforce schema-valid JSON output
    response = await ollama_client.chat(
        model=await get_ollama_model(),
        messages=[
            {
                "role": "system",
                "content": OLLAMA_SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": f"Requirements: \n{prompt}"
            }
        ],
        tools=None,
        stream=False,
        think=think,
        format=OllamaChatResponse.model_json_schema()
    )

    # Fail fast if the LLM returns no response
    if response is None:
        raise ValueError("No Local LLM Response from Core LLM")

    # Return structured response
    return response


# def api_llm(prompt: str) -> str:
#     response = client.chat.completions.create(
#         model='openai/gpt-oss-120b:free',
#         messages=[
#             {
#                 "role": "user",
#                 "content": prompt
#             }
#         ]
#     )

#     return f"LLM response for: {response}"


# if __name__ == "__main__":
#     local_llm("What is today's date?")
