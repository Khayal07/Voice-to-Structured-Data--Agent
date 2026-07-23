"""Async SQLAlchemy engine, session factory, and startup helpers."""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import get_settings
from app.db.models import Base

_settings = get_settings()

engine = create_async_engine(_settings.database_url, future=True, pool_pre_ping=True)

SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency yielding an async DB session."""
    async with SessionLocal() as session:
        yield session


async def init_db() -> None:
    """Create tables if they don't exist (simple bootstrap; Alembic is future work)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
