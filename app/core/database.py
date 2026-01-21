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
    connect_args=None,
    convert_unicode=None,
    creator=None,
    echo=None,
    echo_pool=None,
    enable_from_linting=None,
    execution_options=None,
    future=None,
    hide_parameters=None,
    implicit_returning=None,
    insertmanyvalues_page_size=None,
    isolation_level=None,
    json_deserializer=None,
    json_serializer=None,
    label_length=None,
    logging_name=None,
    max_identifier_length=None,
    max_overflow=20,
    module=None,
    paramstyle=None,
    pool=None,
    poolclass=None,
    pool_logging_name=None,
    pool_pre_ping=True,
    pool_size=10,
    pool_recycle=None,
    pool_reset_on_return=None,
    pool_timeout=None,
    pool_use_lifo=False,
    plugins=None,
    query_cache_size=None,
    use_insertmanyvalues=False,
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
