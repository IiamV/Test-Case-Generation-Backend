# Configuration management

from pydantic import ConfigDict
from pydantic_settings import BaseSettings
import os
from dotenv import load_dotenv
import logger


load_dotenv()

log = logger.logger


class Settings(BaseSettings):
    # app_name: str = "AI Test Platform"
    # llm_provider: str = "openai"

    # Unused bool variable
    use_local_llm: bool = True

    # FastAPI settings
    FASTAPI_SECRET_KEY: str | None = os.getenv("FASTAPI_SECRET_KEY")

    # LLM settings
    LOCAL_LLM_MODEL: str | None = os.getenv("LOCAL_LLM_MODEL")
    EMBED_MODEL: str | None = os.getenv("EMBED_MODEL")

    # Database settings
    DATABASE_URL: str | None = os.getenv("DATABASE_URL")

    # Jira settings
    JIRA_CLIENT_ID: str | None = os.getenv("JIRA_CLIENT_ID")
    JIRA_SECRET: str | None = os.getenv("JIRA_SECRET")
    JIRA_REDIRECT_URL: str | None = os.getenv("JIRA_REDIRECT_URL")


settings = Settings()
