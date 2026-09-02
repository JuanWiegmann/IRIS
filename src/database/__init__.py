"""
Database Package
================

PostgreSQL + pgvector database layer for KIM.

Main exports:
- DatabaseConfig: Connection configuration
- init_engine, get_engine, get_session: Connection management
- All ORM models (UserProfileModel, UserToneModel, etc.)
"""

from src.database.config import (
    DatabaseConfig,
    init_engine,
    get_engine,
    get_session,
    get_sessionmaker,
    close_engine,
)

from src.database.models import (
    Base,
    UserProfileModel,
    UserToneModel,
    UserBoundaryModel,
    UserProjectModel,
    UserOutputModel,
    MemoryEntryModel,
    OnboardingTargetModel,
)

__all__ = [
    # Config
    "DatabaseConfig",
    "init_engine",
    "get_engine",
    "get_session",
    "get_sessionmaker",
    "close_engine",
    # Models
    "Base",
    "UserProfileModel",
    "UserToneModel",
    "UserBoundaryModel",
    "UserProjectModel",
    "UserOutputModel",
    "MemoryEntryModel",
    "OnboardingTargetModel",
]
