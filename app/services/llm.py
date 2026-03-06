from app.core.llm import local_llm_chat
from app.models.ollama import OllamaChatRequest
from app.utils.utils import format_issue_descriptions
from app.core.postman import create_request
import json
from typing import Optional, Dict, Any, List
from app.utils.utils import parse_requirements_from_text


async def generate_tests(collectionId: str, request: OllamaChatRequest) -> Optional[Dict[str, Any]]:
    """
    Generates system-level testcases from a structured Jira issue description using a local OLLAMA server.

    Args:
        request (OllamaChatRequest): A structured request containing a list of Jira issue descriptions to be analyzed.

    Returns:
        Optional[Dict[str, Any]]: A JSON-compatible dictionary containing the LLM-generated system-level testcases if successful, or None if no valid output is produced.
    """

    # Legacy method: accept list of issue descriptions and generate requests
    formatted_requirements = await format_issue_descriptions(request.issue_descriptions)

    # Invoke the local LLM to generate system-level testcases (single-shot for aggregated input)
    content = await local_llm_chat(
        prompt=formatted_requirements,
        think=request.think
    )

    for req in content:
        payload = req.model_dump(mode="json")
        await create_request(collection_id=collectionId, payload=payload)

    return


async def generate_tests_from_issues(
    collectionId: str,
    issues: list[dict],
    think: bool = False,
    tests_per_requirement: int = 3,
    test_types: List[str] = None,
    push_to_postman: bool = True,
) -> int:
    """Generate testcases per requirement extracted from provided issues.

    issues: list of dicts with keys: 'key' and 'description' (and optionally 'summary')
    For each issue, parse requirements from description and call LLM per requirement.
    Returns number of pushed requests.
    """
    pushed = 0

    for issue in issues:
        issue_key = issue.get("key")
        description = issue.get("description") or issue.get("summary") or ""

        # parse requirements from description
        requirements = parse_requirements_from_text(description)

        # If no explicit requirements found, treat whole description as single requirement
        if not requirements:
            if description.strip():
                requirements = [description.strip()]
            else:
                continue

        # Generate per requirement
        for req_text in requirements:
            # Build an explicit prompt requesting structured JSON testcases
            types_list = test_types or ["happy", "edge", "negative"]
            prompt = (
                f"Generate {tests_per_requirement} test cases for the following requirement.\n"
                f"Requirement: {req_text}\n"
                f"Focus on these test types: {', '.join(types_list)}.\n"
                "Return a JSON array where each element is an object with keys: \n"
                "  - title (string)\n"
                "  - preconditions (string)\n"
                "  - steps (array of strings)\n"
                "  - expected_result (string)\n"
                "  - severity (one of low, medium, high)\n"
                "Do not include any explanatory text outside the JSON array."
            )

            content = await local_llm_chat(prompt=prompt, think=think)

            # Normalize LLM output to a Python list of dicts
            data = None
            if isinstance(content, str):
                try:
                    data = json.loads(content)
                except Exception:
                    # fallback: try to parse first JSON block inside the string
                    try:
                        start = content.index("[")
                        end = content.rindex("]") + 1
                        data = json.loads(content[start:end])
                    except Exception:
                        data = []
            elif isinstance(content, list):
                data = [c.model_dump(mode="json") if hasattr(c, "model_dump") else dict(c) for c in content]
            else:
                data = []

            for item in data:
                # item may be a dict or a pydantic-like model
                if hasattr(item, "model_dump"):
                    payload_dict = item.model_dump(mode="json")
                else:
                    payload_dict = dict(item)

                title = payload_dict.get("title") or payload_dict.get("name") or "Generated Test"
                pre = payload_dict.get("preconditions", "")
                steps = payload_dict.get("steps", []) or []
                expected = payload_dict.get("expected_result", payload_dict.get("expected", ""))
                severity = payload_dict.get("severity", "medium")

                # Compose a minimal Postman request payload storing the testcase details in the body
                postman_payload = {
                    "name": title,
                    "request": {
                        "method": "POST",
                        "header": [],
                        "body": {
                            "mode": "raw",
                            "raw": (
                                f"Preconditions:\n{pre}\n\nSteps:\n"
                                + "\n".join([f"- {s}" for s in steps])
                                + f"\n\nExpected:\n{expected}"
                            ),
                        },
                    },
                    "description": f"Source Jira: {issue_key}. Requirement: {req_text}\n\nSeverity: {severity}",
                }

                if push_to_postman:
                    await create_request(collection_id=collectionId, payload=postman_payload)
                pushed += 1

    return pushed


async def generate_testcases_from_issues(
    issues: list[dict],
    think: bool = False,
    tests_per_requirement: int = 3,
    test_types: List[str] | None = None,
) -> list:
    """Generate structured testcases from provided issues without pushing to Postman.

    Returns a list of generated test entries:
      [{"issue_key": str, "requirement": str, "tests": [dict, ...]}, ...]
    """
    results = []

    for issue in issues:
        issue_key = issue.get("key")
        description = issue.get("description") or issue.get("summary") or ""

        requirements = parse_requirements_from_text(description)
        if not requirements:
            if description.strip():
                requirements = [description.strip()]
            else:
                continue

        for req_text in requirements:
            types_list = test_types or ["happy", "edge", "negative"]
            prompt = (
                f"Generate {tests_per_requirement} test cases for the following requirement.\n"
                f"Requirement: {req_text}\n"
                f"Focus on these test types: {', '.join(types_list)}.\n"
                "Return a JSON array where each element is an object with keys: \n"
                "  - title (string)\n"
                "  - preconditions (string)\n"
                "  - steps (array of strings)\n"
                "  - expected_result (string)\n"
                "  - severity (one of low, medium, high)\n"
                "Do not include any explanatory text outside the JSON array."
            )

            content = await local_llm_chat(prompt=prompt, think=think)

            data = None
            if isinstance(content, str):
                try:
                    data = json.loads(content)
                except Exception:
                    try:
                        start = content.index("[")
                        end = content.rindex("]") + 1
                        data = json.loads(content[start:end])
                    except Exception:
                        data = []
            elif isinstance(content, list):
                data = [c.model_dump(mode="json") if hasattr(c, "model_dump") else dict(c) for c in content]
            else:
                data = []

            # normalize items
            normalized = []
            for item in data:
                if hasattr(item, "model_dump"):
                    payload_dict = item.model_dump(mode="json")
                else:
                    payload_dict = dict(item)
                normalized.append(payload_dict)

            results.append({"issue_key": issue_key, "requirement": req_text, "tests": normalized})

    return results
