from fastapi import APIRouter
from fastapi.responses import JSONResponse
from app.models.ollama import OllamaChatRequest, OllamaChatResponse
from app.services.llm import generate_tests
from app.models.ollama import OllamaChatResponse

router = APIRouter()


@router.api_route(
    path="/testcases",
    response_model=OllamaChatResponse,
    summary="Generate Testcases",
    description="Generate testcases from Jira issues using LLMs",
    responses={200: {"model": OllamaChatResponse,
                     "description": "Testcases Successfully Generated"}},
    methods=["POST"],
    response_class=JSONResponse,
)
async def get_testcases(request: OllamaChatRequest):
    # Delegate request handling to the LLM service layer
    return await generate_tests(request=request)
