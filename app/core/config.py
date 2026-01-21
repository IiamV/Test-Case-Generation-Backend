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
    use_local_llm: bool = True
    # OPENAI_API_KEY: str | None = os.getenv("LLM_API_KEY")
    # OPENAI_MODEL: str | None = os.getenv("OPENAI_MODEL")

    LOCAL_LLM_MODEL: str | None = os.getenv("LOCAL_LLM_MODEL")
    EMBED_MODEL: str | None = os.getenv("EMBED_MODEL")
    DATABASE_URL: str | None = os.getenv("DATABASE_URL")

    JIRA_CLIENT_ID: str | None = os.getenv("JIRA_CLIENT_ID")
    JIRA_SECRET: str | None = os.getenv("JIRA_SECRET")
    JIRA_REDIRECT_URL: str | None = os.getenv("JIRA_REDIRECT_URL")


settings = Settings()
