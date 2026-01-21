#  This file is for defining the models within the schemas

from pydantic import BaseModel
from typing import List


class TestCase(BaseModel):
    id: str
    description: str
    steps: List[str]
    inputs: List[str]
    preconditions: List[str]
    expected_result: str
    postconditions: List[str]


class SystemResponse(BaseModel):
    status: str
    message: str
