from fastapi import Request, HTTPException, Header
from typing import Optional
from app.core.postman import get_user
from fastapi.responses import RedirectResponse
from authlib.integrations.httpx_client import OAuth2Client
from app.core.config import settings
from app.core.postman import get_user
from app.core.cache import cache_set, cache_get
import secrets

jira_scope = ["read:me", "read:jira-user", "read:jira-work", "offline_access"]
jira_auth_base_url = "https://auth.atlassian.com/authorize"
jira_token_url = "https://auth.atlassian.com/oauth/token"
jira_audience = "api.atlassian.com"
jira_oauth = OAuth2Client(
    client_id=settings.JIRA_CLIENT_ID,
    scope=" ".join(jira_scope),
    redirect_uri=settings.JIRA_REDIRECT_URL
)


async def jira_login(request: Request) -> RedirectResponse:

    authorization_url, state = jira_oauth.create_authorization_url(
        url=jira_auth_base_url,
        audience=jira_audience,
    )

    request.session["oauth_state"] = state
    return RedirectResponse(authorization_url)


async def jira_callback(request: Request) -> RedirectResponse:
    returned_state = request.query_params.get("state")
    expected_state = request.session.get("oauth_state")

    if not expected_state or returned_state != expected_state:
        raise HTTPException(
            status_code=400,
            detail="Invalid OAuth state"
        )

    token_json = jira_oauth.fetch_token(
        url=jira_token_url,
        client_secret=settings.JIRA_SECRET,
        authorization_response=str(request.url)
    )

    # jira_token = JiraToken.model_validate(token_json)
    session_token = _generate_token()

    await cache_set(
        key=session_token,
        value={
            "jira": token_json,
            "postman": None
        },
        expire_at=token_json['expires_at']
    )

    response = RedirectResponse(f"http://localhost:5173/dashboard/projects#{session_token}")

    return response


async def postman_connect(session_token: str, key: str) -> Optional[bool]:
    session = await cache_get(session_token)

    if session is None:
        return False

    user = await get_user(key)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid Postman API Key")

    session['postman'] = key
    await cache_set(
        key=session_token,
        value=session
    )
    return True


def _generate_token() -> str:
    return secrets.token_urlsafe(32)


async def verify_postman_session(x_session_token: str = Header(...)):

    session = await cache_get(x_session_token)
    if session is None:
        raise HTTPException(status_code=401, detail="Invalid session key")

    key = session['postman']
    if key is None:
        raise HTTPException(status_code=401, detail="Missing Postman API Key")

    user = await get_user(key)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid Postman API Key")

    return key


async def verify_session(x_session_token: str = Header(...)):
    session = await cache_get(x_session_token)
    if session is None:
        raise HTTPException(status_code=401, detail="Invalid session")

    return x_session_token


async def verify_jira_session(x_session_token: str = Header(...)):
    session = await cache_get(x_session_token)

    if session is None:
        raise HTTPException(status_code=401, detail="Invalid session key")

    key = session['jira']
    if key is None:
        raise HTTPException(status_code=401, detail="Missing Jira Key")

    return key
