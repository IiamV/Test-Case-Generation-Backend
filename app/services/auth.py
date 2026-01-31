from fastapi import Request, HTTPException
from fastapi.responses import RedirectResponse
from fastapi import Request
from authlib.integrations.httpx_client import OAuth2Client
from app.core.config import settings
from app.models.jira import JiraToken
from app.core.cache import cache_set

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

    jira_token = JiraToken.model_validate(token_json)
    await cache_set(
        key="jira_token",
        value=jira_token,
        expire_at=jira_token.expires_at
    )

    return RedirectResponse("/health")
