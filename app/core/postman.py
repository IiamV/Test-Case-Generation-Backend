import requests
from typing import Literal, Any, List
from app.core.config import settings
from app.models.postman import PostmanRequest
import httpx


POSTMAN_URLS = {
    'collections': 'https://api.getpostman.com/collections',
    'environments': 'https://api.getpostman.com/environments',
    'workspaces': 'https://api.getpostman.com/workspaces',
    'user': 'https://api.getpostman.com/users/me',
    'mocks': 'https://api.getpostman.com/mocks',
    'monitors': 'https://api.getpostman.com/monitors',
    'postbot': 'https://api.getpostman.com/postbot/generations/tool',
}

def _build_headers(api_key: str | None = None) -> dict:
    key = api_key or settings.POSTMAN_API_KEY
    return {"X-Api-Key": key} if key else {}


def get_all_collections(api_key: str | None = None):
    headers = _build_headers(api_key)
    response = requests.get(url=POSTMAN_URLS['collections'], headers=headers)
    return response.json()


def get_collection(collection_id: str, api_key: str | None = None):
    headers = _build_headers(api_key)
    response = requests.get(url=f"{POSTMAN_URLS['collections']}/{collection_id}", headers=headers)
    return response.json()


def get_all_workspaces(api_key: str | None = None):
    headers = _build_headers(api_key)
    response = requests.get(url=POSTMAN_URLS['workspaces'], headers=headers)
    return response.json()


async def create_request(collection_id: str, payload: Any, api_key: str | None = None) -> Any:
    url = f"{POSTMAN_URLS['collections']}/{collection_id}/requests"

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(
            url=url,
            headers=_build_headers(api_key),
            json=payload,
        )
        response.raise_for_status()
        return response.json()


def get_all_requestIds(collection_id: str):
    collection = get_collection(collection_id=collection_id)
    result = []

    for request in collection["collection"]["item"]:
        result.append(request['id'])

    return result


def get_user(api_key: str | None = None):
    headers = _build_headers(api_key)
    response = requests.get(url=POSTMAN_URLS['user'], headers=headers)
    return response.json()


def postbot_generate(
        collectionId: str,
        requestId: str,
        language: str,
        agentFramework: str
) -> Any:

    POSTBOT_PAYLOAD = {
        "collectionId": collectionId,
        "requestId": requestId,
        "config": {
            "language": language,
            "agentFramework": agentFramework
        }
    }

    response = requests.post(
        url=POSTMAN_URLS['postbot'],
        headers=_build_headers(),
        json=POSTBOT_PAYLOAD
    )

    return response.json()
