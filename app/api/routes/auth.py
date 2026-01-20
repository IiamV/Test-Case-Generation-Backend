from fastapi import APIRouter
from app.services.auth import jira_login

router = APIRouter()


@router.post("/jira-login")
def jira_login():
    jira_login()
    return
