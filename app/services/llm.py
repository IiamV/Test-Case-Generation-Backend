from app.core.llm import local_llm_chat
from app.models.ollama import OllamaChatRequest
from app.services.utils import format_issue_descriptions
import json
from typing import Optional, Dict, Any


async def generate_tests(request: OllamaChatRequest) -> Optional[Dict[str, Any]]:
    """
    Generates system-level testcases from a structured Jira issue description using a local OLLAMA server.

    Args:
        request (OllamaChatRequest): A structured request containing a list of Jira issue descriptions to be analyzed.

    Returns:
        Optional[Dict[str, Any]]: A JSON-compatible dictionary containing the LLM-generated system-level testcases if successful, or None if no valid output is produced.
    """

    # Normalize and aggregate issue descriptions into LLM-ready requirements
    formatted_requirements = await format_issue_descriptions(request.issue_descriptions)

    # Invoke the local LLM to generate system-level testcases
    content = await local_llm_chat(
        prompt=formatted_requirements,
        think=request.think
    )

    # Parse and return the LLM-generated JSON payload if present
    if content and content.message and content.message.content:
        return json.loads(content.message.content)

    # Explicitly return None when no valid LLM output is produced
    return None
