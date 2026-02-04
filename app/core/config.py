# Configuration management
from pydantic_settings import BaseSettings
import os
from dotenv import load_dotenv


# Load environment variables from .env into process environment
load_dotenv()


class Settings(BaseSettings):
    # FastAPI settings
    FASTAPI_SECRET_KEY: str | None = os.getenv("FASTAPI_SECRET_KEY")

    # LLM settings
    OLLAMA_HOST: str = os.getenv(
        "OLLAMA_HOST", 'http://localhost:11434')
    LOCAL_LLM_MODEL: str = os.getenv(
        "LOCAL_LLM_MODEL", 'tinyllama:latest')
    LOCAL_EMBED_MODEL: str = os.getenv(
        "LOCAL_EMBED_MODEL", 'nomic-embed-text:latest')
    CUSTOM_LLM_MODEL: str = os.getenv(
        "CUSTOM_LLM_MODEL", 'swd-model:latest')

    # Database settings
    DATABASE_URL: str | None = os.getenv("DATABASE_URL")

    # Cache settings
    REDIS_USERNAME: str | None = os.getenv("REDIS_USERNAME")
    REDIS_PASSWORD: str | None = os.getenv("REDIS_PASSWORD")
    REDIS_HOST: str = os.getenv("REDIS_HOST", 'localhost')
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", 6379))

    # Jira settings
    JIRA_CLIENT_ID: str | None = os.getenv("JIRA_CLIENT_ID")
    JIRA_SECRET: str | None = os.getenv("JIRA_SECRET")
    JIRA_REDIRECT_URL: str | None = os.getenv("JIRA_REDIRECT_URL")


# Singleton settings instance shared across the application
settings = Settings()
