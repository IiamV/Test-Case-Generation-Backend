from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
from app.core.postman import get_all_collections, get_collection, create_request
from app.services.postman import generate_test_script, generate_all_test_scripts
from app.models.postman import PostmanTestScriptRequest, PostmanTestScriptsRequest, PostmanRequest
from typing import List

router = APIRouter()


@router.api_route(
    path="/collections",
    # response_model=GenericResponse,
    summary="",
    description="Gets all user's collections",
    responses={200: {"description": "Successfully retrieved"}},
    methods=["GET"],
    response_class=JSONResponse,
)
async def all_collections():
    collections = get_all_collections()

    return collections


@router.api_route(
    path="/collection",
    # response_model=,
    summary="Get specific collection by ID",
    description="",
    responses={200: {"description": "Successfully retrieved"}},
    methods=["GET"],
    response_class=JSONResponse,
)
async def collection(
    collectionId: str = Query(
        description="Postman collection ID",
        strict=True
    )
):
    collection = get_collection(collection_id=collectionId)

    return JSONResponse(
        content=collection
    )


@router.api_route(
    path="/generate",
    # response_model=GenericResponse,
    summary="Get specific collection by ID",
    description="",
    responses={200: {"description": "Successfully retrieved"}},
    methods=["GET"],
    response_class=JSONResponse,
)
async def testscript(request: PostmanTestScriptRequest):
    collection = generate_test_script(
        collectionId=request.collectionId,
        requestId=request.requestId,
        language=request.language.value,
        agentFramework=request.agentFramework.value
    )

    return JSONResponse(
        content=collection
    )


@router.api_route(
    path="/generate-all",
    response_model=List[PostmanRequest],
    summary="Get specific collection by ID",
    description="",
    responses={200: {"description": "Successfully retrieved"}},
    methods=["GET"],
    response_class=JSONResponse,
)
async def testscripts(request: PostmanTestScriptsRequest):
    collections = generate_all_test_scripts(
        collectionId=request.collectionId,
        language=request.language.value,
        agentFramework=request.agentFramework.value
    )

    return JSONResponse(
        content=collections
    )


@router.api_route(
    path="/requests",
    # response_model=List[PostmanRequest],
    summary="Get specific collection by ID",
    description="",
    responses={200: {"description": "Successfully retrieved"}},
    methods=["POST"],
    response_class=JSONResponse,
)
async def request(collectionId: str, request: PostmanRequest):
    collections = create_request(
        collection_id=collectionId,
        payload=request
    )

    return JSONResponse(
        content=collections
    )
