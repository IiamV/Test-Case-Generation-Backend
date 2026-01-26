# database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import (
    DeclarativeBase,
    sessionmaker,
    Session,
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer, text, Engine
from app.core.config import settings
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine, async_sessionmaker, AsyncAttrs, AsyncSession
from sqlalchemy_utils import database_exists, create_database


class Base(AsyncAttrs, DeclarativeBase):
    pass


async def get_engine() -> AsyncEngine:
    # if not database_exists(settings.DATABASE_URL):
    #     create_database(settings.DATABASE_URL)

    engine = create_async_engine(
        url=str(settings.DATABASE_URL),
        # connect_args={"sslmode": "require"},
        max_overflow=20,
        pool_pre_ping=True,
        pool_size=10
    )

    return engine


async def get_session() -> AsyncSession:
    engine = await get_engine()

    async_session = async_sessionmaker(
        bind=engine,
        autoflush=False
    )()

    return async_session


async def database_healthcheck() -> None:
    engine = await get_engine()

    async with engine.connect() as connection:
        await connection.execute(text("SELECT 1"))
