"""
Profile Package
===============

User profile management for IRIS.

Main exports:
- UserProfile: Pydantic model for user profiles
- ProfileStore: CRUD operations
- get_or_create_profile: Main entry point
"""

from src.profile.schema import (
    UserProfile,
    Tone,
    FormatPreference,
    create_default_profile,
    format_profile_for_llm,
)

from src.profile.store import (
    get_or_create_profile,
    get_default_store as get_profile_store,
)

from src.profile.store import (
    profile_exists,
    get_profile,
)

__all__ = [
    # Schema
    "UserProfile",
    "Tone",
    "FormatPreference",
    "create_default_profile",
    "format_profile_for_llm",
    # Store
    "get_or_create_profile",
    "get_profile_store",
    "profile_exists",
    "get_profile",
]
