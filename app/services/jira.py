from fastapi import HTTPException
import httpx
import logging
import requests
from atlassian.jira import Jira
from app.core.config import settings
from app.models.jira import JiraToken
from app.core.cache import cache_get

ATLASSIAN_RESOURCES_URL = "https://api.atlassian.com/oauth/token/accessible-resources"


async def _get_access_token() -> str:
    try:
        jira_token = await cache_get(key="jira_token")
        if jira_token is None:
            raise HTTPException(
                status_code=401,
                detail="Jira user token not found in storage"
            )

        jira_token = JiraToken.model_validate(jira_token)
        access_token = jira_token.access_token
    except HTTPException as e:
        raise
    except Exception as e:
        raise RuntimeError(f"Failed to get Jira access token: {e}")
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


async def get_all_jira_projects(token: str | None = None):
    """Return all Jira projects. If `token` is provided it will be used,
    otherwise the token will be taken from the cache/storage.
    """
    if token:
        access_token = token
    else:
        access_token = await _get_access_token()

    jira = await _create_jira_client(access_token)
    return jira.projects()


async def get_all_jira_issues(project_name: str, token: str | None = None):
    """Return all Jira issues for a project. If `token` is provided it will be used.
    """
    if token:
        access_token = token
    else:
        access_token = await _get_access_token()

    if project_name is None:
        raise HTTPException(
            status_code=404,
            detail="No project name found in query params"
        )

    jira = await _create_jira_client(access_token)

    # TODO: May subjugate under SQL Injection
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

    return issues


async def create_issues_from_requirements(
    project_key: str,
    requirements: list,
    issue_type: str = "Task",
    token: str | None = None,
):
    """Create Jira issues from a list of requirement strings.

    Returns list of created issue keys/ids.
    """
    if token:
        access_token = token
    else:
        access_token = await _get_access_token()

    jira = await _create_jira_client(access_token)

    issues_payload = []
    for req in requirements:
        fields = {
            "project": {"key": project_key},
            "summary": req if isinstance(req, str) else req.get("summary", "Requirement"),
            "description": req if isinstance(req, str) else req.get("description", ""),
            "issuetype": {"name": issue_type},
        }
        issues_payload.append({"fields": fields})

    # Use create_issues for bulk creation when available
    try:
        created = jira.create_issues(issues_payload)
    except requests.exceptions.HTTPError as e:
        # Surface upstream HTTP error from Jira with status and body
        resp = getattr(e, "response", None)
        body = None
        status = 500
        if resp is not None:
            try:
                body = resp.text
                status = getattr(resp, "status_code", 500)
            except Exception:
                body = str(e)
        logging.exception("Jira create_issues HTTPError")
        raise HTTPException(status_code=status, detail=f"Jira API error: {body}")
    except Exception:
        # Fallback: create one by one, surface any HTTP errors
        created = []
        for payload in issues_payload:
            try:
                res = jira.create_issue(fields=payload["fields"])
                created.append(res)
            except requests.exceptions.HTTPError as e:
                resp = getattr(e, "response", None)
                body = None
                status = 500
                if resp is not None:
                    try:
                        body = resp.text
                        status = getattr(resp, "status_code", 500)
                    except Exception:
                        body = str(e)
                logging.exception("Jira create_issue HTTPError (fallback)")
                raise HTTPException(status_code=status, detail=f"Jira API error: {body}")

    # Normalize response to contain keys/ids
    result = []
    for item in created:
        if isinstance(item, dict):
            result.append({"id": item.get("id"), "key": item.get("key")})
        else:
            # atlassian library may return strings or objects
            try:
                result.append({"id": item.id, "key": item.key})
            except Exception:
                result.append({"repr": str(item)})

    return result
