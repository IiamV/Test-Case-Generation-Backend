#  This file is for defining the models within the schemas

from pydantic import BaseModel
from typing import List


class SystemResponse(BaseModel):
    status: str
    message: str
