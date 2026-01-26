from fastapi import APIRouter
from app.core.database import database_healthcheck
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from app.core.database import get_engine
from app.core.llm import ollama_healthcheck
from app.core.vector_database import chromadb_healthcheck, chromadb_client
from chromadb.errors import ChromaError
from app.models.schemas import SystemResponse

router = APIRouter()


@router.api_route(
    path="/health",
    response_model=SystemResponse,
    summary="Health Check",
    description="Checks the health",
    responses={200: {"description": "Services Healthy"}},
    methods=["GET"],
    response_class=JSONResponse,
)
async def healthcheck():
    return JSONResponse(
        status_code=200,
        content={
            "status": "ok",
            "message": "Backend is up and running"
        },
    )


@router.api_route(
    path="/status",
    response_model=SystemResponse,
    summary="Services Status Check",
    description="Checks the status of the service (LLM, Database, Vector Database)",
    responses={200: {"description": "Services Healthy"},
               503: {"description": "Service Unavailable"}},
    methods=["GET"],
    response_class=JSONResponse,
)
async def status():
    db_ok: bool = True
    llm_ok: bool = True
    vector_ok: bool = True

    try:
        await database_healthcheck()
    except SQLAlchemyError as e:
        print("Database healthcheck failed:", e)
        db_ok = False

    try:
        await ollama_healthcheck()
    except Exception as e:
        print("LLM healthcheck failed:", e)
        llm_ok = False

    try:
        chromadb_healthcheck()
    except ChromaError as e:
        print("ChromaDB healthcheck failed:", e)
        vector_ok = False

    if not db_ok or not llm_ok or not vector_ok:
        errorMessage = f"Database: {db_ok}, LLM: {llm_ok}, Vector: {vector_ok}"

        return JSONResponse(
            status_code=503,
            content={
                "status": "error",
                "message": errorMessage
            },
        )

    return JSONResponse(
        status_code=200,
        content={
            "status": "ok",
            "message": "Database, LLM, and Vector services healthy"
        },
    )
