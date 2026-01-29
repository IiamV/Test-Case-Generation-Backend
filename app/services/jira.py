from fastapi import Request, HTTPException
import httpx
from starlette.middleware.sessions import SessionMiddleware
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi import FastAPI, Request
from atlassian.jira import Jira
from authlib.integrations.httpx_client import OAuth2Client
from app.core.config import settings
import json
from typing import Dict
from app.models.jira import AllJiraIssuesResponse
from app.services.utils import inspect_schema
from app.models.jira import JiraToken

ATLASSIAN_RESOURCES_URL = "https://api.atlassian.com/oauth/token/accessible-resources"


async def _get_access_token(request: Request) -> str:
    access_token = request.session.get("jira_access_token")
    if access_token is None:
        raise HTTPException(
            status_code=404,
            detail="No token json found in session"
        )
    return access_token


async def _get_cloud_id(access_token: str) -> str:
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(
            ATLASSIAN_RESOURCES_URL,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json",
            },
        )
        response.raise_for_status()

        resources = response.json()

    if not resources:
        raise Exception("No resources found")

    return resources[0]["id"]


async def _create_jira_client(access_token: str) -> Jira:
    cloud_id = await _get_cloud_id(access_token)

    oauth2_config = {
        "client_id": settings.JIRA_CLIENT_ID,
        "token": {
            "access_token": access_token,
            "token_type": "Bearer",
        },
    }

    return Jira(
        url=f"https://api.atlassian.com/ex/jira/{cloud_id}",
        oauth2=oauth2_config,
        cloud=True,
    )


async def get_all_jira_projects(request: Request):
    access_token = await _get_access_token(request)

    jira = await _create_jira_client(access_token)
    return jira.projects()


async def get_all_jira_issues(request: Request):
    access_token = await _get_access_token(request)

    project_name = request.query_params.get("project_name")
    if project_name is None:
        raise HTTPException(
            status_code=404,
            detail="No project name found in query params"
        )

    jira = await _create_jira_client(access_token)

    jql_request = f'project = "{project_name}" ORDER BY issuekey'
    issues = jira.enhanced_jql(
        jql=jql_request,
        fields=[
            'description',
            'id',
            'key',
            'self',
            'statusCategory',
            'summary'
        ]
    )

    if issues is None:
        return AllJiraIssuesResponse(issues=[], isLast=True)

    return issues
