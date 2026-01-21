#  This file is for LLM abstraction layer
import ollama
from app.core.config import settings
from openai import OpenAI
import logger
from typing import Sequence
import httpx

# client = OpenAI()
log = logger.logger


async def ollama_healthcheck() -> None:
    async with httpx.AsyncClient(timeout=1.0) as client:
        response = await client.get("http://localhost:11434/api/tags")
        response.raise_for_status()


def local_llm(prompt: str) -> str | None:
    response = ollama.chat(model=str(settings.LOCAL_LLM_MODEL),
                           messages=[
                           {
                               "role": "user",
                               "content": prompt
                           }
                           ],
                           tools=None,
                           stream=False,
                           think=False,
                           format=None,
                           options=None,
                           keep_alive=None
                           )

    logger.logger.info(
        "LLM response: %s", response.model_dump_json(indent=1),
    )
    if response is None:
        raise ValueError("None Local LLM Response from Core LLM")

    if response.message.content is not None:
        return response.message.content


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
