from fastapi import APIRouter

router = APIRouter()


@router.api_route("/healthcheck", methods=["GET"])
def healthcheck():
    return {"message": "FastAPI is up and running!"}
