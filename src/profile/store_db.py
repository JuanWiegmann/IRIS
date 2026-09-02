"""
Profile Storage (Database Backend)
===================================

Database-backed implementation of ProfileStore using PostgreSQL + pgvector.

Maintains the same interface as the file-based store for compatibility.
"""

from typing import Optional
from uuid import UUID
from datetime import datetime

from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload

from src.database import get_sessionmaker, UserProfileModel, UserToneModel, UserBoundaryModel, UserProjectModel
from src.profile.schema import UserProfile, Tone, FormatPreference, create_default_profile


# ═══════════════════════════════════════════════════════════
# CONVERSION FUNCTIONS (Pydantic ↔ SQLAlchemy)
# ═══════════════════════════════════════════════════════════

def orm_to_pydantic(orm_profile: UserProfileModel) -> UserProfile:
    """
    Convert SQLAlchemy model to Pydantic model.

    Args:
        orm_profile: UserProfileModel with relationships loaded

    Returns:
        UserProfile Pydantic model
    """
    # Extract tones (sorted by priority)
    tones = [Tone(t.tone) for t in sorted(orm_profile.tones, key=lambda x: x.priority)]

    # Extract boundaries as dict
    boundaries = {b.category: b.rule for b in orm_profile.boundaries}

    # Extract active projects
    projects = [p.project_name for p in orm_profile.projects if p.is_active]

    return UserProfile(
        id=orm_profile.id,
        language=orm_profile.language,
        tone=tones,
        format_preference=FormatPreference(orm_profile.format_preference),
        boundaries=boundaries,
        confidence=float(orm_profile.confidence),
        created_at=orm_profile.created_at,
        updated_at=orm_profile.updated_at,
        current_projects=projects,
        recent_context=orm_profile.recent_context or "",
    )


async def pydantic_to_orm(profile: UserProfile, session) -> UserProfileModel:
    """
    Convert Pydantic model to SQLAlchemy model with relationships.

    Args:
        profile: UserProfile Pydantic model
        session: Database session

    Returns:
        UserProfileModel with relationships
    """
    # Create core profile
    orm_profile = UserProfileModel(
        id=profile.id,
        language=profile.language,
        format_preference=profile.format_preference.value,
        confidence=profile.confidence,
        recent_context=profile.recent_context or None,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )

    # Add tones
    for idx, tone in enumerate(profile.tone, start=1):
        orm_profile.tones.append(UserToneModel(
            tone=tone.value,
            priority=idx
        ))

    # Add boundaries
    for category, rule in profile.boundaries.items():
        orm_profile.boundaries.append(UserBoundaryModel(
            category=category,
            rule=rule
        ))

    # Add projects
    for project_name in profile.current_projects:
        orm_profile.projects.append(UserProjectModel(
            project_name=project_name,
            is_active=True
        ))

    return orm_profile


# ═══════════════════════════════════════════════════════════
# DATABASE STORE CLASS
# ═══════════════════════════════════════════════════════════

class ProfileStoreDB:
    """
    Database-backed profile storage.

    Implements the same interface as ProfileStore for compatibility.
    """

    async def create(self, profile: UserProfile) -> UserProfile:
        """
        Create a new profile.

        Args:
            profile: The profile to create

        Returns:
            The created profile

        Raises:
            ValueError: If profile already exists
        """
        async with get_sessionmaker()() as session:
            async with session.begin():
                # Check if exists
                result = await session.execute(
                    select(UserProfileModel).where(UserProfileModel.id == profile.id)
                )
                if result.scalar_one_or_none() is not None:
                    raise ValueError(f"Profile {profile.id} already exists")

                # Convert and add
                orm_profile = await pydantic_to_orm(profile, session)
                session.add(orm_profile)

        return profile

    async def read(self, user_id: UUID) -> Optional[UserProfile]:
        """
        Read a profile by user ID.

        Args:
            user_id: The user's UUID

        Returns:
            The profile, or None if not found
        """
        async with get_sessionmaker()() as session:
            # Load profile with all relationships
            result = await session.execute(
                select(UserProfileModel)
                .where(UserProfileModel.id == user_id)
                .options(
                    selectinload(UserProfileModel.tones),
                    selectinload(UserProfileModel.boundaries),
                    selectinload(UserProfileModel.projects)
                )
            )
            orm_profile = result.scalar_one_or_none()

            if orm_profile is None:
                return None

            return orm_to_pydantic(orm_profile)

    async def save(self, profile: UserProfile) -> None:
        """
        Save a profile (create or update).

        Updates the updated_at timestamp automatically.

        Args:
            profile: The profile to save
        """
        profile.updated_at = datetime.utcnow()

        async with get_sessionmaker()() as session:
            async with session.begin():
                # Check if exists
                result = await session.execute(
                    select(UserProfileModel).where(UserProfileModel.id == profile.id)
                )
                existing = result.scalar_one_or_none()

                if existing is None:
                    # Create new
                    orm_profile = await pydantic_to_orm(profile, session)
                    session.add(orm_profile)
                else:
                    # Update existing: delete old relationships, create new
                    # Delete old tones, boundaries, projects
                    await session.execute(
                        delete(UserToneModel).where(UserToneModel.user_id == profile.id)
                    )
                    await session.execute(
                        delete(UserBoundaryModel).where(UserBoundaryModel.user_id == profile.id)
                    )
                    await session.execute(
                        delete(UserProjectModel).where(UserProjectModel.user_id == profile.id)
                    )

                    # Update core fields
                    existing.language = profile.language
                    existing.format_preference = profile.format_preference.value
                    existing.confidence = profile.confidence
                    existing.recent_context = profile.recent_context or None
                    existing.updated_at = profile.updated_at

                    # Add new relationships
                    for idx, tone in enumerate(profile.tone, start=1):
                        session.add(UserToneModel(
                            user_id=profile.id,
                            tone=tone.value,
                            priority=idx
                        ))

                    for category, rule in profile.boundaries.items():
                        session.add(UserBoundaryModel(
                            user_id=profile.id,
                            category=category,
                            rule=rule
                        ))

                    for project_name in profile.current_projects:
                        session.add(UserProjectModel(
                            user_id=profile.id,
                            project_name=project_name,
                            is_active=True
                        ))

    async def delete(self, user_id: UUID) -> bool:
        """
        Delete a profile.

        Args:
            user_id: The user's UUID

        Returns:
            True if deleted, False if not found
        """
        async with get_sessionmaker()() as session:
            async with session.begin():
                result = await session.execute(
                    delete(UserProfileModel)
                    .where(UserProfileModel.id == user_id)
                    .returning(UserProfileModel.id)
                )
                return result.scalar_one_or_none() is not None

    async def exists(self, user_id: UUID) -> bool:
        """
        Check if a profile exists.

        Args:
            user_id: The user's UUID

        Returns:
            True if exists, False otherwise
        """
        async with get_sessionmaker()() as session:
            result = await session.execute(
                select(UserProfileModel.id).where(UserProfileModel.id == user_id)
            )
            return result.scalar_one_or_none() is not None

    async def list_all(self) -> list[UUID]:
        """
        List all profile IDs.

        Returns:
            List of UUIDs for all stored profiles
        """
        async with get_sessionmaker()() as session:
            result = await session.execute(
                select(UserProfileModel.id)
            )
            return [row[0] for row in result.all()]


# ═══════════════════════════════════════════════════════════
# CONVENIENCE FUNCTIONS
# ═══════════════════════════════════════════════════════════

async def get_or_create_profile_db(user_id: UUID) -> UserProfile:
    """
    Get an existing profile or create a default one (database version).

    Args:
        user_id: The user's UUID

    Returns:
        The user's profile
    """
    store = ProfileStoreDB()
    profile = await store.read(user_id)

    if profile is None:
        # Create default profile
        profile = create_default_profile()
        profile.id = user_id
        await store.create(profile)

    return profile


# ═══════════════════════════════════════════════════════════
# DEFAULT STORE INSTANCE
# ═══════════════════════════════════════════════════════════

_default_store_db: Optional[ProfileStoreDB] = None


def get_default_store_db() -> ProfileStoreDB:
    """
    Get the default ProfileStoreDB instance (singleton).
    """
    global _default_store_db
    if _default_store_db is None:
        _default_store_db = ProfileStoreDB()
    return _default_store_db
