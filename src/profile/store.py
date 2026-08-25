"""
Profile Storage
===============

CRUD operations for user profiles.

Storage strategy:
- File-based (JSON) for Segment 2 (simple, portable)
- One file per profile: ~/.kim/data/profiles/{user_id}.json
- Async I/O (non-blocking)

Future considerations (Segment 9):
- Database (PostgreSQL, SQLite) for multi-user deployments
- Encryption at rest
- Backup/versioning
"""

import json
from pathlib import Path
from typing import Optional
from uuid import UUID

import aiofiles

from src.profile.schema import UserProfile, create_default_profile


# ═══════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════

# Default data directory
DEFAULT_DATA_DIR = Path.home() / ".kim" / "data" / "profiles"


# ═══════════════════════════════════════════════════════════
# STORAGE CLASS
# ═══════════════════════════════════════════════════════════

class ProfileStore:
    """
    Manages user profile persistence.

    Async operations for non-blocking I/O.
    """

    def __init__(self, data_dir: Optional[Path] = None):
        """
        Initialize the profile store.

        Args:
            data_dir: Directory for profile storage (defaults to ~/.kim/data/profiles)
        """
        self.data_dir = data_dir or DEFAULT_DATA_DIR
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def _profile_path(self, user_id: UUID) -> Path:
        """Get the file path for a user's profile."""
        return self.data_dir / f"{user_id}.json"

    async def create(self, profile: UserProfile) -> UserProfile:
        """
        Create a new profile.

        Args:
            profile: The profile to create

        Returns:
            The created profile

        Raises:
            FileExistsError: If profile already exists
        """
        path = self._profile_path(profile.id)

        if path.exists():
            raise FileExistsError(f"Profile {profile.id} already exists")

        await self.save(profile)
        return profile

    async def read(self, user_id: UUID) -> Optional[UserProfile]:
        """
        Read a profile by user ID.

        Args:
            user_id: The user's UUID

        Returns:
            The profile, or None if not found
        """
        path = self._profile_path(user_id)

        if not path.exists():
            return None

        async with aiofiles.open(path, "r", encoding="utf-8") as f:
            content = await f.read()
            data = json.loads(content)
            return UserProfile(**data)

    async def save(self, profile: UserProfile) -> None:
        """
        Save a profile (create or update).

        Updates the updated_at timestamp automatically.

        Args:
            profile: The profile to save
        """
        from datetime import datetime
        profile.updated_at = datetime.utcnow()

        path = self._profile_path(profile.id)

        # Write atomically (write to temp file, then rename)
        temp_path = path.with_suffix(".tmp")

        async with aiofiles.open(temp_path, "w", encoding="utf-8") as f:
            # Pydantic v2: model_dump() instead of dict()
            data = profile.model_dump(mode="json")
            await f.write(json.dumps(data, indent=2, default=str))

        # Atomic rename (overwrites existing)
        temp_path.replace(path)

    async def delete(self, user_id: UUID) -> bool:
        """
        Delete a profile.

        Args:
            user_id: The user's UUID

        Returns:
            True if deleted, False if not found
        """
        path = self._profile_path(user_id)

        if not path.exists():
            return False

        path.unlink()
        return True

    async def exists(self, user_id: UUID) -> bool:
        """
        Check if a profile exists.

        Args:
            user_id: The user's UUID

        Returns:
            True if exists, False otherwise
        """
        return self._profile_path(user_id).exists()

    async def list_all(self) -> list[UUID]:
        """
        List all profile IDs.

        Returns:
            List of UUIDs for all stored profiles
        """
        profile_files = self.data_dir.glob("*.json")
        return [UUID(path.stem) for path in profile_files]


# ═══════════════════════════════════════════════════════════
# CONVENIENCE FUNCTIONS
# ═══════════════════════════════════════════════════════════

async def get_or_create_profile(
    user_id: UUID,
    store: Optional[ProfileStore] = None
) -> UserProfile:
    """
    Get an existing profile or create a default one.

    This is the main entry point for loading user profiles.

    Args:
        user_id: The user's UUID
        store: ProfileStore instance (creates default if None)

    Returns:
        The user's profile
    """
    if store is None:
        store = ProfileStore()

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

# Singleton instance for convenience
_default_store: Optional[ProfileStore] = None


def get_default_store() -> ProfileStore:
    """
    Get the default ProfileStore instance (singleton).

    Creates it on first call.
    """
    global _default_store
    if _default_store is None:
        _default_store = ProfileStore()
    return _default_store
