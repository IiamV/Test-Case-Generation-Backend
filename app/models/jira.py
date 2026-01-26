from pydantic import BaseModel, HttpUrl
from typing import List


# ==================JIRA ISSUES MODELS===============================================================
class IssueFieldsStatusCategory(BaseModel):
    self: str
    id: int
    key: str
    colorName: str
    name: str


class IssueFields(BaseModel):
    summary: str
    statusCategory: IssueFieldsStatusCategory
    description: str


class JiraIssue(BaseModel):
    expand: str
    id: str
    self: HttpUrl
    key: str
    fields: IssueFields


class AllJiraIssuesResponse(BaseModel):
    issues: List[JiraIssue]
    isLast: bool
