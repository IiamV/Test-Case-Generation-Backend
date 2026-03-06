from fastapi import Request, HTTPException
import logging
from fastapi.responses import RedirectResponse
from fastapi import Request
from authlib.integrations.httpx_client import OAuth2Client
from app.core.config import settings
from app.models.jira import JiraToken
from app.core.cache import cache_set
from urllib.parse import urlencode
import httpx

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
    # Store expected oauth state in session and log for local debugging
    request.session["oauth_state"] = state
    logging.getLogger("uvicorn.error").debug("Jira login state: state=%s url=%s", state, authorization_url)

    return RedirectResponse(authorization_url)


async def jira_callback(request: Request) -> RedirectResponse:
    returned_state = request.query_params.get("state")
    expected_state = request.session.get("oauth_state")

    logging.getLogger("uvicorn.error").debug("Jira callback state: returned=%s expected=%s session_keys=%s",
                                               returned_state, expected_state, list(request.session.keys()))

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

    jira_token = JiraToken.model_validate(token_json)
    await cache_set(
        key="jira_token",
        value=jira_token,
        expire_at=jira_token.expires_at
    )

    # Fetch user info immediately
    user_info = await get_jira_user_info(jira_token.access_token)
    
    # Redirect to frontend with access token and user info in query params
    import json
    user_info_json = json.dumps(user_info["user"])
    redirect_url = f"{settings.FRONTEND_URL}?{urlencode({'token': jira_token.access_token, 'user': user_info_json})}"
    return RedirectResponse(redirect_url)


async def get_jira_user_info(token: str) -> dict:
    """Fetch current user info from Jira using access token."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.atlassian.com/me",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/json"
            }
        )
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail="Failed to fetch user info from Jira"
            )
        
        user_data = response.json()
        return {
            "user": {
                "id": user_data.get("account_id"),
                "name": user_data.get("name"),
                "email": user_data.get("email"),
                "avatar": user_data.get("picture")
            }
        }
