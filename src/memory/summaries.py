"""
Conversation Summaries
=====================

Compressed summaries of past conversations.

When STM fills up, old messages are compressed into summaries.
Summaries preserve context while reducing token usage.

Storage: File-based, one summary per conversation session.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Optional
from uuid import UUID

from src.storage.file_store import get_iris_root


# ═══════════════════════════════════════════════════════════
# STORAGE
# ═══════════════════════════════════════════════════════════

def get_summaries_path(user_id: UUID) -> Path:
    """Get path to user's summaries file."""
    iris_root = get_iris_root()
    summaries_dir = iris_root / "data" / "memory" / "summaries"
    summaries_dir.mkdir(parents=True, exist_ok=True)
    return summaries_dir / f"{user_id}_summaries.json"


def load_summaries(user_id: UUID) -> list[dict]:
    """
    Load summaries for user.

    Args:
        user_id: User UUID

    Returns:
        List of summaries (newest first)
    """
    path = get_summaries_path(user_id)

    if not path.exists():
        return []

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return data.get("summaries", [])


def save_summaries(user_id: UUID, summaries: list[dict]) -> None:
    """
    Save summaries for user.

    Args:
        user_id: User UUID
        summaries: Summaries to save
    """
    path = get_summaries_path(user_id)

    with open(path, "w", encoding="utf-8") as f:
        json.dump({
            "summaries": summaries,
            "updated_at": datetime.utcnow().isoformat()
        }, f, indent=2)


# ═══════════════════════════════════════════════════════════
# API
# ═══════════════════════════════════════════════════════════

def create_summary(
    user_id: UUID,
    summary_text: str,
    message_count: int,
    topics: Optional[list[str]] = None
) -> None:
    """
    Create a conversation summary.

    Args:
        user_id: User UUID
        summary_text: Summary content
        message_count: Number of messages summarized
        topics: Optional list of topics covered
    """
    summaries = load_summaries(user_id)

    summaries.append({
        "summary": summary_text,
        "message_count": message_count,
        "topics": topics or [],
        "created_at": datetime.utcnow().isoformat()
    })

    save_summaries(user_id, summaries)


def get_summaries(
    user_id: UUID,
    limit: Optional[int] = None
) -> list[dict]:
    """
    Get recent summaries.

    Args:
        user_id: User UUID
        limit: Optional limit (default: all)

    Returns:
        List of summaries (newest first)
    """
    summaries = load_summaries(user_id)

    if limit:
        return summaries[-limit:]

    return summaries


def compress_old_messages(
    user_id: UUID,
    messages: list[dict],
    summary_text: str
) -> None:
    """
    Compress old STM messages into a summary.

    Call this when STM is full and needs compression.

    Args:
        user_id: User UUID
        messages: Messages to compress
        summary_text: Generated summary
    """
    # Extract topics (simple keyword extraction)
    topics = extract_topics(messages)

    # Create summary
    create_summary(
        user_id=user_id,
        summary_text=summary_text,
        message_count=len(messages),
        topics=topics
    )


def extract_topics(messages: list[dict]) -> list[str]:
    """
    Extract main topics from messages (simple keyword approach).

    Args:
        messages: List of messages

    Returns:
        List of topic keywords
    """
    # Simple: collect frequent nouns (basic implementation)
    # Production: use NLP or LLM-based topic extraction

    all_text = " ".join([m["content"] for m in messages])
    words = all_text.lower().split()

    # Filter common words (basic stop words)
    stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for"}
    keywords = [w for w in words if len(w) > 4 and w not in stop_words]

    # Get top 5 most common
    from collections import Counter
    common = Counter(keywords).most_common(5)

    return [word for word, count in common]


def format_summaries_for_llm(summaries: list[dict]) -> str:
    """
    Format summaries for LLM.

    Args:
        summaries: List of summary dicts

    Returns:
        Markdown-formatted summaries
    """
    if not summaries:
        return "*(No conversation history)*"

    lines = []

    for idx, summary in enumerate(summaries[-5:], start=1):  # Last 5 summaries
        created_at = summary.get("created_at", "")
        summary_text = summary["summary"]
        topics = summary.get("topics", [])
        message_count = summary.get("message_count", 0)

        # Format date
        if created_at:
            dt = datetime.fromisoformat(created_at)
            date_str = dt.strftime("%Y-%m-%d")
            lines.append(f"### Summary {idx} ({date_str})")
        else:
            lines.append(f"### Summary {idx}")

        lines.append(f"*{message_count} messages*")

        if topics:
            lines.append(f"*Topics: {', '.join(topics)}*")

        lines.append("")
        lines.append(summary_text.strip())
        lines.append("")
        lines.append("---")
        lines.append("")

    return "\n".join(lines)
