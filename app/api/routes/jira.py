from typing import List

from fastapi import APIRouter, HTTPException, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.services.jira import create_issues_from_requirements, get_all_jira_projects
from app.services.jira import ATLASSIAN_RESOURCES_URL
import httpx
from app.core.config import settings
from app.core.cache import cache_set
import time
from pydantic import BaseModel
from typing import Dict, Any, Optional
from app.services.llm import generate_testcases_from_issues, generate_tests_from_issues

router = APIRouter()


class CreateIssuesRequest(BaseModel):
    project_key: str
    requirements: List[str]
    issue_type: str | None = "Task"


class GenerateTestcasesRequest(BaseModel):
    # Either provide `issues` (list of {key, description|summary})
    # or provide `project` + `issueKeys` so server can fetch issues.
    project: Optional[str] = None
    issueKeys: Optional[List[str]] = None
    issues: Optional[List[Dict[str, Any]]] = None
    testsPerRequirement: int = 3
    testTypes: Optional[List[str]] = None
    think: bool = False


@router.post(
    "/create-issues",
    response_class=JSONResponse,
    summary="Create Jira issues from selected requirements",
)
async def create_issues(payload: CreateIssuesRequest, authorization: str | None = Header(None)):
    if not payload.requirements:
        raise HTTPException(status_code=400, detail="No requirements provided")

    token = None
    if authorization:
        parts = authorization.split()
        if len(parts) == 2 and parts[0] == "Bearer":
            token = parts[1]
        else:
            raise HTTPException(status_code=401, detail="Invalid Authorization header format")

    created = await create_issues_from_requirements(
        project_key=payload.project_key,
        requirements=payload.requirements,
        issue_type=payload.issue_type or "Task",
        token=token,
    )

    return {"created": created}


@router.get("/projects", response_class=JSONResponse)
async def list_projects():
    projects = await get_all_jira_projects()
    return {"projects": projects}


@router.post("/generate-testcases", response_class=JSONResponse)
async def generate_testcases(payload: GenerateTestcasesRequest, authorization: str | None = Header(None)):
    """Generate AI testcases from provided issues or by fetching issues from Jira.

    Returns a list of generated test entries grouped by issue+requirement.
    """
    issues_to_process = []

    if payload.issues:
        issues_to_process = payload.issues
    else:
        if not payload.project or not payload.issueKeys:
            raise HTTPException(status_code=400, detail="Either 'issues' or both 'project' and 'issueKeys' must be provided")

        token = None
        if authorization:
            parts = authorization.split()
            if len(parts) == 2 and parts[0] == "Bearer":
                token = parts[1]
            else:
                raise HTTPException(status_code=401, detail="Invalid Authorization header format")

        # fetch all issues for the project, then filter by keys
        issues_resp = await get_all_jira_issues(project_name=payload.project, token=token)
        if isinstance(issues_resp, dict) and "issues" in issues_resp:
            all_issues = issues_resp["issues"]
        else:
            all_issues = issues_resp

        # filter by keys
        for i in all_issues:
            if i.get("key") in payload.issueKeys:
                issues_to_process.append({"key": i.get("key"), "description": i.get("fields", {}).get("description"), "summary": i.get("fields", {}).get("summary")})

    # Call LLM service to generate testcases (do not push to Postman)
    generated = await generate_testcases_from_issues(
        issues=issues_to_process,
        think=payload.think,
        tests_per_requirement=payload.testsPerRequirement,
        test_types=payload.testTypes,
    )

    return {"generated": generated}


@router.get("/validate-token", response_class=JSONResponse)
async def validate_token(authorization: str | None = Header(None)):
    """Validate a Bearer token against Atlassian accessible-resources and return the resources JSON.

    Use header: `Authorization: Bearer <token>`
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    parts = authorization.split()
    if len(parts) != 2 or parts[0] != "Bearer":
        raise HTTPException(status_code=401, detail="Invalid Authorization header format")

    token = parts[1]

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(
            ATLASSIAN_RESOURCES_URL,
            headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
        )

    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=f"Jira token validation failed: {resp.text}")

    return resp.json()


@router.get("/oauth/callback", response_class=JSONResponse)
async def jira_oauth_callback(code: str | None = None, state: str | None = None):
    """OAuth callback to exchange authorization code for access token and persist it in cache.

    The Jira authorization server will redirect the user to this endpoint with `code` and `state`.
    """
    if not code:
        raise HTTPException(status_code=400, detail="Missing code parameter")

    token_url = "https://auth.atlassian.com/oauth/token"
    payload = {
        "grant_type": "authorization_code",
        "client_id": settings.JIRA_CLIENT_ID,
        "client_secret": settings.JIRA_SECRET,
        "code": code,
        "redirect_uri": settings.JIRA_REDIRECT_URL,
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(token_url, json=payload, headers={"Accept": "application/json"})

    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=f"Token exchange failed: {resp.text}")

    token_json = resp.json()

    # Persist token in cache for later use
    try:
        expire_in = token_json.get("expires_in")
        await cache_set("jira_token", token_json, expire_in=expire_in)
    except Exception:
        # Do not fail the exchange if cache write fails; just log
        pass

    return {"status": "ok", "token": token_json}
