"""
Short-Term Memory (STM)
=======================

Recent conversation context (last N messages).

Storage: In-memory for current session, file-based for persistence.
Default: Keep last 10 messages (5 user + 5 assistant pairs).

Use case: Provide immediate conversation context to LLM.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Optional
from uuid import UUID
from collections import deque

from src.storage.file_store import get_iris_root


# ═══════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════

DEFAULT_STM_SIZE = 10  # Last 10 messages


# ═══════════════════════════════════════════════════════════
# STORAGE
# ═══════════════════════════════════════════════════════════

def get_stm_path(user_id: UUID) -> Path:
    """Get path to user's STM file."""
    iris_root = get_iris_root()
    stm_dir = iris_root / "data" / "memory" / "stm"
    stm_dir.mkdir(parents=True, exist_ok=True)
    return stm_dir / f"{user_id}_stm.json"


def load_stm(user_id: UUID, max_size: int = DEFAULT_STM_SIZE) -> list[dict]:
    """
    Load STM messages for user.

    Args:
        user_id: User UUID
        max_size: Maximum messages to keep

    Returns:
        List of recent messages (oldest first)
    """
    path = get_stm_path(user_id)

    if not path.exists():
        return []

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    messages = data.get("messages", [])

    # Return only last N
    return messages[-max_size:] if len(messages) > max_size else messages


def save_stm(user_id: UUID, messages: list[dict]) -> None:
    """
    Save STM messages for user.

    Args:
        user_id: User UUID
        messages: Messages to save
    """
    path = get_stm_path(user_id)

    with open(path, "w", encoding="utf-8") as f:
        json.dump({
            "messages": messages,
            "updated_at": datetime.utcnow().isoformat()
        }, f, indent=2)


# ═══════════════════════════════════════════════════════════
# API
# ═══════════════════════════════════════════════════════════

def store_message(
    user_id: UUID,
    role: str,
    content: str,
    max_size: int = DEFAULT_STM_SIZE
) -> None:
    """
    Store a message in STM.

    Args:
        user_id: User UUID
        role: "user" or "assistant"
        content: Message content
        max_size: Max STM size
    """
    messages = load_stm(user_id, max_size)

    messages.append({
        "role": role,
        "content": content,
        "timestamp": datetime.utcnow().isoformat()
    })

    # Keep only last N
    if len(messages) > max_size:
        messages = messages[-max_size:]

    save_stm(user_id, messages)


def get_recent_messages(
    user_id: UUID,
    limit: Optional[int] = None
) -> list[dict]:
    """
    Get recent messages from STM.

    Args:
        user_id: User UUID
        limit: Optional limit (default: all STM)

    Returns:
        List of messages (oldest first)
    """
    messages = load_stm(user_id)

    if limit:
        return messages[-limit:]

    return messages


def clear_stm(user_id: UUID) -> None:
    """
    Clear STM for user.

    Args:
        user_id: User UUID
    """
    save_stm(user_id, [])


def format_stm_for_llm(messages: list[dict]) -> str:
    """
    Format STM messages for LLM.

    Args:
        messages: List of message dicts

    Returns:
        Markdown-formatted conversation
    """
    if not messages:
        return "*(No recent conversation)*"

    lines = []

    for msg in messages:
        role = msg["role"].capitalize()
        content = msg["content"]
        timestamp = msg.get("timestamp", "")

        # Format timestamp
        if timestamp:
            dt = datetime.fromisoformat(timestamp)
            time_str = dt.strftime("%H:%M")
            lines.append(f"**{role}** ({time_str})")
        else:
            lines.append(f"**{role}**")

        lines.append(content.strip())
        lines.append("")

    return "\n".join(lines)
