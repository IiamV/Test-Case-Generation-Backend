# Application entry point and composition root

from fastapi import FastAPI
from app.api.routes import system
from app.core import llm

app = FastAPI(title="AI Testcase Generation, Monitoring and Execution")

# app.include_router(srs.router, prefix="/srs", tags=["SRS"])
# app.include_router(testcases.router, prefix="/testcases", tags=["Testcases"])
# app.include_router(execution.router, prefix="/execution", tags=["Execution"])
# app.include_router(monitoring.router, prefix="/monitoring",
#                    tags=["Monitoring"])

app.include_router(system.router, tags=["System Health"])
# app.include_router(testcases.router)


# if __name__ == "__main__":
#     print("Hello World")
