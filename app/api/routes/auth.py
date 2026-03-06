from fastapi import APIRouter
from app.services.auth import jira_login, jira_callback, get_jira_user_info
from app.models.schemas import JiraAuthResponse
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi import Request, Header, HTTPException

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


@router.get("/debug-oauth-state", response_class=JSONResponse)
async def debug_oauth_state(request: Request):
    """Local-only debug endpoint to inspect session oauth_state and session keys."""
    state = request.session.get("oauth_state")
    keys = list(request.session.keys())
    return JSONResponse(status_code=200, content={"oauth_state": state, "session_keys": keys})


@router.get("/jira/me", response_class=JSONResponse)
async def get_jira_me(authorization: str = Header(None)):
    """Get current Jira user info.
    
    Headers:
        Authorization: Bearer {token}
    
    Returns:
        {"user": {"id", "name", "email", "avatar"}}
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    
    # Extract token from "Bearer {token}" format
    parts = authorization.split()
    if len(parts) != 2 or parts[0] != "Bearer":
        raise HTTPException(status_code=401, detail="Invalid Authorization header format")
    
    token = parts[1]
    result = await get_jira_user_info(token)
    return JSONResponse(status_code=200, content=result)
