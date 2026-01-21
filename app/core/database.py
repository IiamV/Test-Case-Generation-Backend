# database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import (
    DeclarativeBase,
    sessionmaker,
    Session,
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer, text
from app.core.config import settings
from sqlalchemy.ext.asyncio import AsyncEngine

engine = create_engine(
    url=str(settings.DATABASE_URL),
    max_overflow=20,
    pool_pre_ping=True,
    pool_size=10
)


class Base(DeclarativeBase):
    pass


SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


def get_session() -> Session:
    return SessionLocal()


async def database_healthcheck(engine: AsyncEngine) -> None:
    async with engine.connect() as connection:
        await connection.execute(text("SELECT 1"))
