import os
from collections.abc import AsyncGenerator

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import (
    DeclarativeBase,
    sessionmaker,
)

DATABASE_URL = os.getenv("DELIVERY_DATABASE_URL", "sqlite:///./delivery.db")


class Base(DeclarativeBase):
    """Base class for SQLAlchemy records."""


engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
    if DATABASE_URL.startswith("sqlite")
    else {},
)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


@event.listens_for(Engine, "connect")
def enable_sqlite_foreign_keys(
    dbapi_connection: object, connection_record: object
) -> None:
    if DATABASE_URL.startswith("sqlite"):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


def init_db() -> None:
    Base.metadata.create_all(engine)


async def get_session() -> AsyncGenerator:
    with SessionLocal() as session:
        yield session
