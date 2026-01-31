from fastapi import APIRouter
from app.services.auth import jira_login, jira_callback
from app.services.jira import get_all_jira_projects
from app.models.schemas import JiraAuthResponse
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi import FastAPI, Request

router = APIRouter()


@router.api_route(
    path="/jira-login",
    response_model=JiraAuthResponse,
    summary="Jira Login",
    description="Redirects to Jira for authorization",
    responses={200: {"description": "Services Healthy"}},
    methods=["GET"],
    response_class=RedirectResponse,
)
async def jira_auth_login(request: Request):
    return await jira_login(request)


@router.api_route(
    path="/jira-callback",
    response_model=JiraAuthResponse,
    summary="Jira Callback",
    description="Redirects to Jira for authorization",
    responses={200: {"description": "Services Healthy"}},
    methods=["GET"],
    response_class=RedirectResponse
)
async def jira_auth_callback(request: Request):
    return await jira_callback(request)
