from fastapi import Request
import httpx
from starlette.middleware.sessions import SessionMiddleware
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi import FastAPI, Request
from atlassian.jira import Jira
from authlib.integrations.httpx_client import OAuth2Client
from app.core.config import settings
from app.services.jira import get_all_jira_projects
from app.models.schemas import GetJiraProjectsResponse
from atlassian import Jira

jira_scope = ["read:me", "read:jira-user", "read:jira-work", "offline_access"]
jira_auth_base_url = "https://auth.atlassian.com/authorize"
jira_token_url = "https://auth.atlassian.com/oauth/token"
jira_audience = "api.atlassian.com"
jira_oauth = OAuth2Client(
    client_id=settings.JIRA_CLIENT_ID,
    scope=" ".join(jira_scope),
    redirect_uri=settings.JIRA_REDIRECT_URL
)

jira = Jira(

)


async def jira_login(request: Request) -> RedirectResponse:

    authorization_url, state = jira_oauth.create_authorization_url(
        url=jira_auth_base_url,
        audience=jira_audience,
    )

    request.session["oauth_state"] = state
    return RedirectResponse(authorization_url)


async def jira_callback(request: Request) -> GetJiraProjectsResponse:

    token_json = jira_oauth.fetch_token(
        url=jira_token_url,
        client_secret=settings.JIRA_SECRET,
        authorization_response=str(request.url)
    )

    # print({
    #     "access_token": token_json["access_token"],
    #     "expires_in": token_json["expires_in"],
    #     "token_type": token_json["token_type"],
    #     "refresh_token": token_json["refresh_token"],
    #     "scope": token_json["scope"],
    #     "expires_at": token_json["expires_at"]
    # })

    projects = get_all_jira_projects(token_json)

    return projects


async def jira_refresh_access():

    jira_oauth.refresh_token(
        url=jira_token_url,
        refresh_token=token_json["refresh_token"]
    )
    return None
