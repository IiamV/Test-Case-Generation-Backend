from fastapi import Request
import httpx
from starlette.middleware.sessions import SessionMiddleware
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi import FastAPI, Request
from atlassian.jira import Jira
from authlib.integrations.httpx_client import OAuth2Client
from app.core.config import settings
from app.models.schemas import GetJiraProjectsResponse
from app.models.outside import JiraProjectsResponse
from app.models.extras import JiraProject
import json


def get_all_jira_projects(token_json) -> JiraProjectsResponse:
    with httpx.Client() as client:
        req = client.get(
            "https://api.atlassian.com/oauth/token/accessible-resources",
            headers={
                "Authorization": f"Bearer {token_json['access_token']}",
                "Accept": "application/json",
            },
        )
        req.raise_for_status()
        resources = req.json()
    cloud_id = resources[0]["id"]
    oauth2_dict = {
        "client_id": settings.JIRA_CLIENT_ID,
        "token": {
            "access_token": token_json["access_token"],
            "token_type": "Bearer",
        },
    }

    jira = Jira(
        url=f"https://api.atlassian.com/ex/jira/{cloud_id}",
        oauth2=oauth2_dict,
        cloud=True
    )

    projects = jira.projects()

    jql_request = 'project = "(Example) Billing System Dev" ORDER BY issuekey'
    issues = jira.enhanced_jql(jql=jql_request, fields=[
        'description', 'id', 'key', 'self', 'statusCategory', 'summary'])
    return projects


def get_all_jira_issues(token_json) -> JiraProjectsResponse:
    with httpx.Client() as client:
        req = client.get(
            "https://api.atlassian.com/oauth/token/accessible-resources",
            headers={
                "Authorization": f"Bearer {token_json['access_token']}",
                "Accept": "application/json",
            },
        )
        req.raise_for_status()
        resources = req.json()
    cloud_id = resources[0]["id"]
    oauth2_dict = {
        "client_id": settings.JIRA_CLIENT_ID,
        "token": {
            "access_token": token_json["access_token"],
            "token_type": "Bearer",
        },
    }

    jira = Jira(
        url=f"https://api.atlassian.com/ex/jira/{cloud_id}",
        oauth2=oauth2_dict,
        cloud=True
    )

    jql_request = 'project = "(Example) Billing System Dev" ORDER BY issuekey'
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

    return issues
