"""
Profile Package
===============

User profile management for KIM.

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
    ProfileStore,
    get_or_create_profile,
    get_default_store,
)

__all__ = [
    # Schema
    "UserProfile",
    "Tone",
    "FormatPreference",
    "create_default_profile",
    "format_profile_for_llm",
    # Store
    "ProfileStore",
    "get_or_create_profile",
    "get_default_store",
]
