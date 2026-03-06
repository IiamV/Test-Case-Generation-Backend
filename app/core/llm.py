# LLM abstraction layer for interacting with a local Ollama server
from ollama import AsyncClient, ChatResponse
from app.core.config import settings
from typing import List, Optional
import httpx
import traceback
from app.models.ollama import OllamaChatResponse
from app.models.postman import PostmanRequest
from typing import List
from pydantic import TypeAdapter
import logging

# System prompt injected into the custom Ollama model to constrain behavior
SWD_MODEL_SYSTEM_PROMPT = """
You are an API request generation assistant.

IMPORTANT — STRICT JSON ONLY:

- Your ONLY output must be a single JSON array (e.g. [ { ... }, { ... } ]). Do NOT output anything else.
- Use valid JSON syntax only: strings must use double quotes, objects/arrays must be properly closed, and escape characters must be correct.
- Do NOT use single quotes for strings. Do NOT include trailing commas.
- Do NOT include explanations, markdown, comments, or any text outside the JSON array.
- If you cannot produce valid JSON, output an empty array: []

SCHEMA REQUIREMENTS (each element must match exactly):
- name: string
- description: string or null
- url: string (absolute URL)
- method: string
- headers: array of { key: string, value: string } (or empty array)
- queryParams: array of { key:string, value:string, equals:boolean, description:string|null, enabled:boolean } OR null
- dataMode: string
- rawModeData: string or null
- dataOptions: { raw: { language: string } }

RULES BY HTTP METHOD:
- GET: method must be "GET", rawModeData must be null, queryParams must list params (or be null).
- POST: method must be "POST", dataMode must be "raw", rawModeData must be a valid JSON string when body required, dataOptions.raw.language must be "json".

ADDITIONAL RULES:
- Do not invent endpoints or fields not in the schema.
- If a field is optional and not applicable, set it to null.
- Ensure array output validates against the provided JSON schema exactly.

Failure behavior: If you cannot comply, return [] (an empty array) and nothing else.
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
                system=SWD_MODEL_SYSTEM_PROMPT
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


async def local_llm_chat(prompt: List[str], think: Optional[bool]) -> List[PostmanRequest]:
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

    schema = TypeAdapter(List[PostmanRequest])

    # Send user requirements to the custom Ollama model and enforce schema-valid JSON output
    response = await ollama_client.chat(
        model=await get_ollama_model(),
        messages=[
            {
                "role": "system",
                "content": SWD_MODEL_SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": f"Requirements: \n{prompt}"
            }
        ],
        tools=None,
        stream=False,
        think=think,
        format=schema.json_schema()
    )

    # Fail fast if the LLM returns no response
    if response is None:
        raise ValueError("No Local LLM Response from Core LLM")

    if response and response.message and response.message.content:
        raw = response.message.content
        try:
            requests_list = schema.validate_json(raw)
        except Exception:
            # Try to extract a JSON array substring from the raw output
            try:
                start = raw.index("[")
                end = raw.rindex("]") + 1
                snippet = raw[start:end]
                requests_list = schema.validate_json(snippet)
            except Exception:
                logging.exception("Failed to validate LLM JSON output")
                # Provide a helpful error containing a snippet of the raw output
                preview = (raw[:1000] + "...") if len(raw) > 1000 else raw
                raise ValueError(f"LLM returned invalid JSON. Preview: {preview}")

    # Return structured response
    return requests_list
