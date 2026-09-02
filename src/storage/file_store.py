"""
File-Based Storage
==================

Local JSON file storage for profiles and outputs.

Storage structure:
~/.kim/
├── profiles/
│   └── {user_id}.json
├── outputs/
│   └── {user_id}/
│       ├── 001_email_team.json
│       └── ...
└── metadata.json
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional
from uuid import UUID

from src.profile.schema import UserProfile, create_default_profile


# ═══════════════════════════════════════════════════════════
# STORAGE ROOT
# ═══════════════════════════════════════════════════════════

def get_kim_root() -> Path:
    """
    Get KIM storage root directory.

    Returns ~/.kim/ and creates it if needed.
    """
    kim_root = Path.home() / ".kim"
    kim_root.mkdir(exist_ok=True)
    return kim_root


# ═══════════════════════════════════════════════════════════
# PROFILE STORE
# ═══════════════════════════════════════════════════════════

class ProfileStore:
    """
    File-based profile storage.

    Stores profiles as JSON files in ~/.kim/profiles/
    """

    def __init__(self, root: Optional[Path] = None):
        """
        Initialize profile store.

        Args:
            root: Storage root (defaults to ~/.kim/)
        """
        self.root = root or get_kim_root()
        self.profiles_dir = self.root / "profiles"
        self.profiles_dir.mkdir(exist_ok=True)

    def _get_profile_path(self, user_id: UUID) -> Path:
        """Get path to user's profile file."""
        return self.profiles_dir / f"{user_id}.json"

    async def create(self, profile: UserProfile) -> UserProfile:
        """
        Create a new profile.

        Args:
            profile: Profile to create

        Returns:
            Created profile

        Raises:
            ValueError: If profile already exists
        """
        path = self._get_profile_path(profile.id)

        if path.exists():
            raise ValueError(f"Profile {profile.id} already exists")

        # Write profile as JSON
        path.write_text(
            json.dumps(profile.model_dump(mode="json"), indent=2, ensure_ascii=False),
            encoding="utf-8"
        )

        return profile

    async def read(self, user_id: UUID) -> Optional[UserProfile]:
        """
        Read a profile by user ID.

        Args:
            user_id: User UUID

        Returns:
            Profile or None if not found
        """
        path = self._get_profile_path(user_id)

        if not path.exists():
            return None

        # Load JSON and create Pydantic model
        data = json.loads(path.read_text(encoding="utf-8"))
        return UserProfile.model_validate(data)

    async def save(self, profile: UserProfile) -> None:
        """
        Save a profile (create or update).

        Updates the updated_at timestamp automatically.

        Args:
            profile: Profile to save
        """
        profile.updated_at = datetime.utcnow()
        path = self._get_profile_path(profile.id)

        # Write profile as JSON
        path.write_text(
            json.dumps(profile.model_dump(mode="json"), indent=2, ensure_ascii=False),
            encoding="utf-8"
        )

    async def delete(self, user_id: UUID) -> bool:
        """
        Delete a profile.

        Args:
            user_id: User UUID

        Returns:
            True if deleted, False if not found
        """
        path = self._get_profile_path(user_id)

        if not path.exists():
            return False

        path.unlink()
        return True

    async def exists(self, user_id: UUID) -> bool:
        """
        Check if a profile exists.

        Args:
            user_id: User UUID

        Returns:
            True if exists
        """
        return self._get_profile_path(user_id).exists()

    async def list_all(self) -> list[UUID]:
        """
        List all profile IDs.

        Returns:
            List of user UUIDs
        """
        return [
            UUID(path.stem)
            for path in self.profiles_dir.glob("*.json")
        ]


# ═══════════════════════════════════════════════════════════
# OUTPUT STORE
# ═══════════════════════════════════════════════════════════

class OutputStore:
    """
    File-based output storage.

    Stores outputs as JSON files in ~/.kim/outputs/{user_id}/
    """

    def __init__(self, root: Optional[Path] = None):
        """
        Initialize output store.

        Args:
            root: Storage root (defaults to ~/.kim/)
        """
        self.root = root or get_kim_root()
        self.outputs_dir = self.root / "outputs"
        self.outputs_dir.mkdir(exist_ok=True)

    def _get_user_dir(self, user_id: UUID) -> Path:
        """Get user's output directory."""
        user_dir = self.outputs_dir / str(user_id)
        user_dir.mkdir(exist_ok=True)
        return user_dir

    def _get_next_output_id(self, user_id: UUID) -> str:
        """Generate next output ID (incremental)."""
        user_dir = self._get_user_dir(user_id)
        existing = list(user_dir.glob("*.json"))

        if not existing:
            return "001"

        # Get highest number
        numbers = [
            int(path.stem.split("_")[0])
            for path in existing
            if path.stem.split("_")[0].isdigit()
        ]

        next_num = max(numbers, default=0) + 1
        return f"{next_num:03d}"

    async def create(
        self,
        user_id: UUID,
        content: str,
        context: str,
        output_type: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> dict:
        """
        Create a new output.

        Args:
            user_id: User UUID
            content: Output content
            context: Context/description
            output_type: Type (email, code, document, etc.)
            metadata: Additional metadata

        Returns:
            Created output dict with id
        """
        user_dir = self._get_user_dir(user_id)
        output_id = self._get_next_output_id(user_id)

        # Create output dict
        output = {
            "id": output_id,
            "content": content,
            "context": context,
            "output_type": output_type,
            "created_at": datetime.utcnow().isoformat(),
            "metadata": metadata or {}
        }

        # Generate filename from context (sanitized)
        context_slug = context.lower().replace(" ", "_")[:30]
        filename = f"{output_id}_{context_slug}.json"
        path = user_dir / filename

        # Write output as JSON
        path.write_text(
            json.dumps(output, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )

        return output

    async def read(self, user_id: UUID, output_id: str) -> Optional[dict]:
        """
        Read a specific output.

        Args:
            user_id: User UUID
            output_id: Output ID (e.g., "001")

        Returns:
            Output dict or None if not found
        """
        user_dir = self._get_user_dir(user_id)

        # Find file starting with output_id
        matches = list(user_dir.glob(f"{output_id}_*.json"))

        if not matches:
            return None

        return json.loads(matches[0].read_text(encoding="utf-8"))

    async def list_all(self, user_id: UUID) -> list[dict]:
        """
        List all outputs for a user.

        Args:
            user_id: User UUID

        Returns:
            List of output dicts (sorted by ID, oldest first)
        """
        user_dir = self._get_user_dir(user_id)
        outputs = []

        for path in sorted(user_dir.glob("*.json")):
            outputs.append(json.loads(path.read_text(encoding="utf-8")))

        return outputs

    async def delete(self, user_id: UUID, output_id: str) -> bool:
        """
        Delete an output.

        Args:
            user_id: User UUID
            output_id: Output ID

        Returns:
            True if deleted, False if not found
        """
        user_dir = self._get_user_dir(user_id)
        matches = list(user_dir.glob(f"{output_id}_*.json"))

        if not matches:
            return False

        matches[0].unlink()
        return True


# ═══════════════════════════════════════════════════════════
# EMBEDDING STORE (Placeholder - Task #2)
# ═══════════════════════════════════════════════════════════

class EmbeddingStore:
    """
    NumPy-based embedding storage.

    Stores embeddings as .npy files in ~/.kim/embeddings/
    """

    def __init__(self, root: Optional[Path] = None):
        """
        Initialize embedding store.

        Args:
            root: Storage root (defaults to ~/.kim/)
        """
        self.root = root or get_kim_root()
        self.embeddings_dir = self.root / "embeddings"
        self.embeddings_dir.mkdir(exist_ok=True)

    # Implementation in Task #2


# ═══════════════════════════════════════════════════════════
# CONVENIENCE FUNCTIONS
# ═══════════════════════════════════════════════════════════

async def get_or_create_profile(user_id: UUID) -> UserProfile:
    """
    Get an existing profile or create a default one.

    Args:
        user_id: User UUID

    Returns:
        User profile
    """
    store = ProfileStore()
    profile = await store.read(user_id)

    if profile is None:
        # Create default profile
        profile = create_default_profile()
        profile.id = user_id
        await store.create(profile)

    return profile


# ═══════════════════════════════════════════════════════════
# DEFAULT STORE INSTANCES (Singleton Pattern)
# ═══════════════════════════════════════════════════════════

_profile_store: Optional[ProfileStore] = None
_output_store: Optional[OutputStore] = None
_embedding_store: Optional[EmbeddingStore] = None


def get_profile_store() -> ProfileStore:
    """Get default ProfileStore instance (singleton)."""
    global _profile_store
    if _profile_store is None:
        _profile_store = ProfileStore()
    return _profile_store


def get_output_store() -> OutputStore:
    """Get default OutputStore instance (singleton)."""
    global _output_store
    if _output_store is None:
        _output_store = OutputStore()
    return _output_store


def get_embedding_store() -> EmbeddingStore:
    """Get default EmbeddingStore instance (singleton)."""
    global _embedding_store
    if _embedding_store is None:
        _embedding_store = EmbeddingStore()
    return _embedding_store
