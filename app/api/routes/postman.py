from fastapi import APIRouter, Query, Body, Header
from fastapi.responses import RedirectResponse
from fastapi.responses import JSONResponse
from app.core.postman import get_all_collections, get_collection, create_request
from app.services.postman import generate_test_script, generate_all_test_scripts, postman_login
from app.models.postman import PostmanTestScriptRequest, PostmanTestScriptsRequest, PostmanRequest
from typing import List
from pydantic import BaseModel


router = APIRouter()



class PushTestcasesRequest(BaseModel):
    collectionId: str
    testcases: List[dict]


@router.post("/push-testcases", response_class=JSONResponse)
async def push_testcases(payload: PushTestcasesRequest, x_api_key: str = Header(None, alias="X-Api-Key")):
    """Push an array of generated testcases into a Postman collection.

    Each testcase should follow the `PostmanRequest` shape defined in `app.models.postman`.
    The endpoint will iterate testcases and call `create_request` for each.
    """
    results = []
    errors = []

    for idx, tc in enumerate(payload.testcases):
        try:
            # create_request expects the payload as the Postman request object
            resp = await create_request(collection_id=payload.collectionId, payload=tc, api_key=x_api_key)
            results.append(resp)
        except Exception as e:
            errors.append({"index": idx, "error": str(e)})

    return JSONResponse(content={"pushed": len(results), "results": results, "errors": errors})


# Login to Postman with API key
class PostmanLoginRequest(BaseModel):
    api_key: str


@router.get("/generate-api-key", response_class=RedirectResponse, summary="Generate Postman API Key")
async def generate_api_key_route():
    """Redirects the client to Postman's API Keys page where they can create/copy a key."""
    from app.services.postman import get_postman_api_key_url
    return RedirectResponse(get_postman_api_key_url())


@router.api_route(
    path="/collections",
    # response_model=GenericResponse,
    summary="",
    description="Gets all user's collections",
    responses={200: {"description": "Successfully retrieved"}},
    methods=["GET"],
    response_class=JSONResponse,
)
async def all_collections(x_api_key: str = Header(..., alias="X-Api-Key")):
    """Get all Postman collections. Provide `X-Api-Key` header (required)."""
    collections = get_all_collections(api_key=x_api_key)

    return JSONResponse(content=collections)


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
    ),
    x_api_key: str = Header(..., alias="X-Api-Key"),
):
    collection = get_collection(collection_id=collectionId, api_key=x_api_key)

    return JSONResponse(content=collection)


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



    
