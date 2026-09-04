"""
Onboarding Session Storage

File-based persistence for onboarding sessions.
Location: ~/.iris/onboarding/{user_id}/{session_id}.json
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from src.onboarding.schema import OnboardingSession


class OnboardingStore:
    """
    Store and retrieve onboarding sessions.

    Storage structure:
    ~/.iris/
      onboarding/
        {user_id}/
          active_session.json         # Current active session
          {session_id}.json          # Completed sessions (history)
          latest.json                # Symlink to most recent
    """

    def __init__(self, base_path: Optional[Path] = None):
        """Initialize store."""
        if base_path is None:
            base_path = Path.home() / ".iris" / "onboarding"
        self.base_path = base_path
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _get_user_dir(self, user_id: str) -> Path:
        """Get user's onboarding directory."""
        user_dir = self.base_path / user_id
        user_dir.mkdir(parents=True, exist_ok=True)
        return user_dir

    def save_session(self, session: OnboardingSession) -> Path:
        """
        Save onboarding session to disk.

        Args:
            session: OnboardingSession to save

        Returns:
            Path to saved file
        """
        user_dir = self._get_user_dir(session.user_id)

        # Determine filename
        if session.is_completed:
            # Completed sessions: use session_id
            filename = f"{session.session_id}.json"
        else:
            # Active session: always overwrite active_session.json
            filename = "active_session.json"

        filepath = user_dir / filename

        # Serialize
        data = session.model_dump(mode="json")

        # Write
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        # Update latest symlink (or copy on Windows)
        latest_path = user_dir / "latest.json"
        try:
            if latest_path.exists():
                latest_path.unlink()
            # Windows doesn't support symlinks easily, just copy
            with open(latest_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception:
            # Symlink failed, ignore (not critical)
            pass

        return filepath

    def load_session(
        self, user_id: str, session_id: Optional[str] = None
    ) -> Optional[OnboardingSession]:
        """
        Load onboarding session from disk.

        Args:
            user_id: User identifier
            session_id: Optional session ID. If None, loads active session.

        Returns:
            OnboardingSession or None if not found
        """
        user_dir = self._get_user_dir(user_id)

        # Determine filename
        if session_id is None:
            # Load active session
            filepath = user_dir / "active_session.json"
        else:
            # Load specific session
            filepath = user_dir / f"{session_id}.json"

        if not filepath.exists():
            return None

        # Read
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Deserialize
        return OnboardingSession.model_validate(data)

    def get_active_session(self, user_id: str) -> Optional[OnboardingSession]:
        """Get user's active (in-progress) onboarding session."""
        return self.load_session(user_id, session_id=None)

    def get_latest_completed_session(self, user_id: str) -> Optional[OnboardingSession]:
        """Get user's most recent completed session."""
        user_dir = self._get_user_dir(user_id)

        # Find all completed sessions
        completed = [
            f for f in user_dir.glob("*.json")
            if f.name not in ["active_session.json", "latest.json"]
        ]

        if not completed:
            return None

        # Sort by modification time (newest first)
        completed.sort(key=lambda p: p.stat().st_mtime, reverse=True)

        # Load most recent
        with open(completed[0], "r", encoding="utf-8") as f:
            data = json.load(f)

        return OnboardingSession.model_validate(data)

    def delete_active_session(self, user_id: str) -> bool:
        """
        Delete user's active session.

        Returns:
            True if deleted, False if not found
        """
        user_dir = self._get_user_dir(user_id)
        filepath = user_dir / "active_session.json"

        if filepath.exists():
            filepath.unlink()
            return True
        return False

    def list_sessions(self, user_id: str) -> list[dict]:
        """
        List all sessions for a user.

        Returns:
            List of session metadata: [{session_id, started_at, completed_at, is_completed}, ...]
        """
        user_dir = self._get_user_dir(user_id)

        sessions = []

        # Load active session
        active = self.get_active_session(user_id)
        if active:
            sessions.append(
                {
                    "session_id": active.session_id,
                    "started_at": active.started_at.isoformat(),
                    "completed_at": None,
                    "is_completed": False,
                    "questions_asked": active.questions_asked,
                    "profile_type": active.profile_type.value if active.profile_type else None,
                }
            )

        # Load completed sessions
        completed_files = [
            f for f in user_dir.glob("*.json")
            if f.name not in ["active_session.json", "latest.json"]
        ]

        for filepath in completed_files:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            sessions.append(
                {
                    "session_id": data["session_id"],
                    "started_at": data["started_at"],
                    "completed_at": data.get("completed_at"),
                    "is_completed": data["is_completed"],
                    "questions_asked": data["questions_asked"],
                    "profile_type": data.get("profile_type"),
                }
            )

        # Sort by started_at (newest first)
        sessions.sort(key=lambda s: s["started_at"], reverse=True)

        return sessions

    def has_completed_onboarding(self, user_id: str) -> bool:
        """Check if user has ever completed onboarding."""
        user_dir = self._get_user_dir(user_id)

        completed_files = [
            f for f in user_dir.glob("*.json")
            if f.name not in ["active_session.json", "latest.json"]
        ]

        return len(completed_files) > 0


# Singleton instance
_store: Optional[OnboardingStore] = None


def get_onboarding_store() -> OnboardingStore:
    """Get singleton onboarding store."""
    global _store
    if _store is None:
        _store = OnboardingStore()
    return _store
