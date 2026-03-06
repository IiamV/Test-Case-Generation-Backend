from typing import Any, List, Iterable


# This function is vibe coded, has been tested but not reviewed
# TODO: Recheck the code and optmize/improve is possible
def _infer_type(value: Any) -> str:
    """
    Infer a human-readable schema type from a Python value.

    Supported types include None, booleans, integers, floats, strings, lists, and dictionaries.

    Returns a string describing the inferred type, such as "null", "boolean", "integer", "number", "string", "array[integer]", "object", or "unknown".
    """

    # Infer a human-readable schema type from a Python value
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return f"array[{_infer_type(value[0])}]" if value else "array[unknown]"
    if isinstance(value, dict):
        return "object"
    return "unknown"


# This function is vibe coded, has been tested but not reviewed
# TODO: Recheck the code and optmize/improve is possible
def inspect_schema(obj: dict, prefix: str = "") -> None:
    """
    Recursively traverse a dictionary and print out the inferred schema type of each value.

    Args:
        obj (dict): A dictionary to be traversed.
        prefix (str, optional): A prefix to be prepended to each key path, if applicable. Defaults to "".
    """

    # Recursively print dot-notation paths with inferred value types
    for key, value in obj.items():
        path = f"{prefix}.{key}" if prefix else key
        print(f"{path}: {_infer_type(value)}")

        if isinstance(value, dict):
            inspect_schema(value, path)
        elif isinstance(value, list) and value and isinstance(value[0], dict):
            inspect_schema(value[0], f"{path}[]")


# This function is vibe coded, has been tested but not reviewed
# TODO: Recheck the code and optmize/improve is possible
async def snake_case_to_title(fields: Iterable[str]) -> List[str]:
    """
    Convert a list of snake_case strings into title case strings.

    Args:
        fields (Iterable[str]): A list of strings in snake case format.

    Returns:
        List[str]: A list of strings in title case format.
    """

    # Convert snake_case field names into human-readable title case
    result = []

    for field in fields:
        words = field.split("_")
        capitalized_words = []

        for word in words:
            capitalized_words.append(word.capitalize())

        title = " ".join(capitalized_words)
        result.append(title)

    return result


async def format_issue_descriptions(issue_descriptions: List[str]) -> List[str]:
    """
    Format a list of issue descriptions into a list of strings with a title case format.

    Args:
        issue_descriptions (List[str]): A list of issue descriptions in snake case format.

    Returns:
        List[str]: A list of strings in title case format.

    Example:
        >>> format_issue_descriptions(["fix bug", "add feature"])
        ["1. Fix Bug", "2. Add Feature"]
    """

    # Prefix issue descriptions with an ordered index for LLM consumption
    result: List[str] = []

    for index, requiremnt in enumerate(issue_descriptions):
        formatted = f"{index+1}. {requiremnt}"
        result.append(formatted)

    return result


def parse_requirements_from_text(text: str) -> List[str]:
    """Parse requirements from Jira formatted issue description.
    
    Handles:
    - Jira headers (h3., h4., etc)
    - Bullet points (*, -, **)
    - AC:/Requirement: prefixes
    
    Returns list of requirement strings.
    """
    import re
    
    if not text:
        return []
    
    lines = text.splitlines()
    requirements = []
    
    # Match Jira headers (h1., h2., h3., etc) or bullet points
    jira_header_rx = re.compile(r"^h[1-6]\.\s*(.+)", re.IGNORECASE)
    bullet_rx = re.compile(r"^\s*(?:[-*•\*]|\d+\.|AC:|Requirement:)\s*(.+)", re.IGNORECASE)
    
    for line in lines:
        # Check for Jira header
        if jira_header_rx.match(line):
            match = jira_header_rx.match(line)
            if match:
                title = match.group(1).strip()
                if title and len(title) > 3:
                    requirements.append(title)
            continue
        
        # Check for bullet points
        if bullet_rx.match(line):
            match = bullet_rx.match(line)
            if match:
                text_part = match.group(1).strip()
                # Remove Jira markup
                text_part = re.sub(r'\*{2,}', '', text_part)
                text_part = text_part.replace('{{', '').replace('}}', '')
                if text_part and len(text_part) > 3:
                    requirements.append(text_part)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_reqs = []
    for req in requirements:
        if req not in seen:
            unique_reqs.append(req)
            seen.add(req)
    
    return unique_reqs
