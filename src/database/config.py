"""
Database Configuration
======================

Connection settings and session management for PostgreSQL + pgvector.
"""

from typing import Optional
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine, AsyncSession, async_sessionmaker


# ═══════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════

class DatabaseConfig(BaseModel):
    """Database connection configuration."""

    host: str = Field(default="localhost")
    port: int = Field(default=5432)
    database: str = Field(default="iris")
    username: str = Field(default="iris")
    password: str = Field(default="iris_dev_password")

    # Connection pool settings
    pool_size: int = Field(default=5)
    max_overflow: int = Field(default=10)
    pool_timeout: int = Field(default=30)

    def get_url(self) -> str:
        """Build asyncpg connection URL."""
        return f"postgresql+asyncpg://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"


# ═══════════════════════════════════════════════════════════
# ENGINE & SESSION MANAGEMENT
# ═══════════════════════════════════════════════════════════

_engine: Optional[AsyncEngine] = None
_sessionmaker: Optional[async_sessionmaker[AsyncSession]] = None


def init_engine(config: Optional[DatabaseConfig] = None) -> AsyncEngine:
    """
    Initialize the database engine.

    Args:
        config: Database configuration (uses defaults if None)

    Returns:
        Configured async engine
    """
    global _engine, _sessionmaker

    if config is None:
        config = DatabaseConfig()

    _engine = create_async_engine(
        config.get_url(),
        echo=False,  # Set to True for SQL logging
        pool_size=config.pool_size,
        max_overflow=config.max_overflow,
        pool_timeout=config.pool_timeout,
        pool_pre_ping=True,  # Verify connections before using
    )

    _sessionmaker = async_sessionmaker(
        _engine,
        class_=AsyncSession,
        expire_on_commit=False,  # Don't expire objects after commit
    )

    return _engine


def get_engine() -> AsyncEngine:
    """Get the current engine (initializes if needed)."""
    global _engine
    if _engine is None:
        init_engine()
    return _engine


def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    """Get the session maker (initializes if needed)."""
    global _sessionmaker
    if _sessionmaker is None:
        init_engine()
    return _sessionmaker


async def get_session() -> AsyncSession:
    """
    Get a new database session.

    Usage:
        async with get_session() as session:
            result = await session.execute(query)
    """
    maker = get_sessionmaker()
    return maker()


async def close_engine():
    """Close the database engine and cleanup connections."""
    global _engine
    if _engine is not None:
        await _engine.dispose()
        _engine = None
