from fastapi import APIRouter, UploadFile, File, HTTPException, status, Request, Header, Query
from fastapi.responses import JSONResponse
from typing import List
from pydantic import BaseModel

from app.services.srs import parse_requirements_from_pdf_bytes
from app.services.jira import get_all_jira_projects, get_all_jira_issues
from app.models.schemas import GenericResponse
from app.models.jira import AllJiraIssuesResponse, JiraProject
from app.services.llm import generate_tests_from_issues


router = APIRouter()


@router.post(
    "/srs/upload",
    response_class=JSONResponse,
    summary="Upload SRS PDF and parse requirements",
    description="Upload a PDF SRS file; server extracts text and returns parsed requirement items.",
)
async def upload_srs(file: UploadFile = File(...)):
    # Only accept PDF
    if file.content_type not in ("application/pdf", "application/octet-stream"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only PDF files are supported")

    data = await file.read()
    try:
        requirements = parse_requirements_from_pdf_bytes(data)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))

    return {"filename": file.filename, "requirements": requirements}


@router.api_route(
    path="/get-jira-projects",
    response_model=List[JiraProject],
    summary="Get All Jira Projects",
    description="Returns all Jira projects",
    responses={200: {"model": List[JiraProject], "description": "Projects Successfully Retrieved"},
               401: {"model": GenericResponse, "description": "Unauthorized"}},
    methods=["GET"],
    response_class=JSONResponse
)
async def get_jira_projects(request: Request, authorization: str = Header(None)):
    """Get all Jira projects. Use Authorization header if provided.
    Header: Authorization: Bearer {token}
    """
    token = None
    if authorization:
        parts = authorization.split()
        if len(parts) != 2 or parts[0] != "Bearer":
            raise HTTPException(status_code=401, detail="Invalid Authorization header format")
        token = parts[1]

    return await get_all_jira_projects(token=token)


@router.api_route(
    path="/get-jira-issues",
    response_model=AllJiraIssuesResponse,
    summary="Get All Jira Issues of a Project",
    description="Returns all Jira issues of a project name that is queried in the parameter",
    responses={200: {"description": "Issues Successfully Retrieved"},
               401: {"model": GenericResponse, "description": "Jira user not authenticated"},
               404: {"model": GenericResponse, "description": "Jira project name not found"}},
    methods=["GET"],
    response_class=JSONResponse
)
async def get_jira_issues(
    project: str = Query(
        description="Jira project name",
        strict=True
    ),
    authorization: str = Header(None)
):
    token = None
    if authorization:
        parts = authorization.split()
        if len(parts) != 2 or parts[0] != "Bearer":
            raise HTTPException(status_code=401, detail="Invalid Authorization header format")
        token = parts[1]

    return await get_all_jira_issues(project_name=project, token=token)


class GenerateToPostmanRequest(BaseModel):
    project: str
    issueKeys: List[str]
    collectionId: str
    think: bool = False
    testsPerRequirement: int = 3
    testTypes: List[str] = None
    pushToPostman: bool = True


@router.api_route(
    path="/generate-to-postman",
    summary="Generate testcases for selected Jira issues and push to Postman",
    description="Select issues from a Jira project and push AI-generated Postman requests into the specified collection",
    methods=["POST"],
    response_class=JSONResponse,
)
async def generate_to_postman(request: GenerateToPostmanRequest, authorization: str = Header(None)):
    # Determine token from header (optional) and fetch all issues for the project
    token = None
    if authorization:
        parts = authorization.split()
        if len(parts) == 2 and parts[0] == "Bearer":
            token = parts[1]

    issues_resp = await get_all_jira_issues(project_name=request.project, token=token)

    # Normalize issues list
    if isinstance(issues_resp, dict) and "issues" in issues_resp:
        issues = issues_resp["issues"]
    else:
        issues = issues_resp

    # Filter selected issues by key
    selected = [i for i in issues if i.get("key") in request.issueKeys]

    if not selected:
        return JSONResponse(status_code=400, content={"detail": "No matching issues found for the provided keys"})

    # Build structured issues list (include issue key and description)
    structured = []
    for idx, issue in enumerate(selected):
        key = issue.get("key")
        fields = issue.get("fields", {})
        description = fields.get("description") or ""
        summary = fields.get("summary") or ""
        structured.append({"key": key, "description": description, "summary": summary})

    # Call per-requirement generator which will push requests and return count
    pushed = await generate_tests_from_issues(
        collectionId=request.collectionId,
        issues=structured,
        think=request.think,
        tests_per_requirement=request.testsPerRequirement,
        test_types=request.testTypes or ["happy", "edge", "negative"],
        push_to_postman=request.pushToPostman,
    )

    return JSONResponse(status_code=200, content={"status": "ok", "pushed": pushed})
