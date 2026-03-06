from app.core.postman import postbot_generate, get_all_requestIds
from typing import Literal
import httpx
from fastapi import HTTPException
import logging


async def postman_login(api_key: str) -> dict:
    """Validate Postman API key by calling /users/me and return user info.

    Logs the remote response and surfaces Postman's response body on error to
    help debugging invalid/revoked keys or API issues.
    """
    url = "https://api.getpostman.com/users/me"
    headers = {"X-Api-Key": api_key, "Accept": "application/json"}
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(url, headers=headers)

    # Log the response (do not log the API key itself)
    logging.getLogger("uvicorn.error").info("Postman login resp.status_code=%s resp.text=%s", resp.status_code, resp.text)

    if resp.status_code != 200:
        detail = resp.text or "Invalid Postman API key or Postman API error"
        # Use Postman's status code if it's an error, otherwise 401
        raise HTTPException(status_code=resp.status_code if resp.status_code >= 400 else 401, detail=detail)

    try:
        return resp.json()
    except Exception:
        return {"data": resp.text}


def get_postman_api_key_url() -> str:
    """Return the Postman web URL where users can create/manage API keys."""
    return "https://web.postman.co/settings/me/api-keys"


def generate_test_script(
        collectionId: str,
        requestId: str,
        language: str,
        agentFramework: str
):
    all_requests = get_all_requestIds(collection_id=collectionId)

    # result = []
    for request in all_requests:

        generated = postbot_generate(
            collectionId=collectionId,
            requestId=request,
            language=language,
            agentFramework=agentFramework
        )

        # result.append(generated['data'])
    return generated


def generate_all_test_scripts(
        collectionId: str,
        language: str,
        agentFramework: str
):
    all_requests = get_all_requestIds(collection_id=collectionId)

    result = []
    for request in all_requests:

        generated = postbot_generate(
            collectionId=collectionId,
            requestId=request,
            language=language,
            agentFramework=agentFramework
        )

        result.append(generated['data']['text'])
    return result



