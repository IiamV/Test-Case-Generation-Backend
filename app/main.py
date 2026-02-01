# Application entry point and composition root

from fastapi import FastAPI
from app.api.routes import system, srs, auth
from app.core import llm
from starlette.middleware.sessions import SessionMiddleware
from app.core.config import settings
from fastapi.openapi.docs import get_swagger_ui_html


app = FastAPI(
    title="AI Testcase Generation, Monitoring and Execution"
)

app.add_middleware(
    SessionMiddleware,
    secret_key=str(settings.FASTAPI_SECRET_KEY),
    same_site="lax",
    # https_only=False,  # True in production with HTTPS
)

# app.include_router(srs.router, prefix="/srs", tags=["SRS"])
# app.include_router(testcases.router, prefix="/testcases", tags=["Testcases"])
# app.include_router(execution.router, prefix="/execution", tags=["Execution"])
# app.include_router(monitoring.router, prefix="/monitoring",
#                    tags=["Monitoring"])

app.include_router(system.router, tags=["System"])
app.include_router(srs.router, tags=["Jira Services"])
app.include_router(auth.router, tags=["Authentication"])
# app.include_router(testcases.router)


# if __name__ == "__main__":
#     print("Hello World")
