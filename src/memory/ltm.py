"""
Long-Term Memory (LTM)
======================

Project memory - major milestones, decisions, technical details.

**ARCHITECTURE DECISION:** LTM = Project Context System (already built).

This module is a wrapper around the existing project_context tools.
No duplication - we reuse what's already there.

Why this makes sense:
- Project memory IS long-term memory
- Already has timeline, query, auto-logging
- Already integrated with profile updates
- No need to build twice

LTM provides:
- Major project milestones
- Architecture decisions
- Technical details
- Collaboration information
- Timeline of changes
"""

from uuid import UUID
from typing import Optional

from src.tools.project_context import (
    get_recent_updates,
    load_project_updates
)


# ═══════════════════════════════════════════════════════════
# LTM API (wraps project_context)
# ═══════════════════════════════════════════════════════════

async def get_ltm_context(
    user_id: UUID,
    project: Optional[str] = None,
    days: int = 30
) -> list[dict]:
    """
    Get long-term memory (project updates).

    Args:
        user_id: User UUID
        project: Specific project (None = all)
        days: How many days back

    Returns:
        List of project updates (newest first)
    """
    # Reuse project_context retrieval
    return get_recent_updates(user_id, project, days)


def get_all_ltm(user_id: UUID) -> dict:
    """
    Get all LTM for user (all projects).

    Args:
        user_id: User UUID

    Returns:
        Dict of {project_name: [updates]}
    """
    return load_project_updates(user_id)


def format_ltm_for_llm(updates: list[dict]) -> str:
    """
    Format LTM for LLM.

    Args:
        updates: List of project updates

    Returns:
        Markdown-formatted timeline
    """
    if not updates:
        return "*(No long-term project memory)*"

    lines = []

    # Group by project
    by_project = {}
    for update in updates:
        proj = update.get("project", "Unknown")
        if proj not in by_project:
            by_project[proj] = []
        by_project[proj].append(update)

    # Format each project
    for project, proj_updates in by_project.items():
        lines.append(f"### {project}")
        lines.append("")

        for upd in proj_updates[:10]:  # Last 10 updates per project
            from datetime import datetime
            timestamp = upd.get("timestamp", "")
            update_text = upd.get("update", "")
            context = upd.get("context", "")
            update_type = upd.get("update_type", "")

            # Format timestamp
            if timestamp:
                dt = datetime.fromisoformat(timestamp)
                date_str = dt.strftime("%Y-%m-%d")
                lines.append(f"**{date_str}** — {update_text}")
            else:
                lines.append(f"• {update_text}")

            if context:
                lines.append(f"  ↳ {context}")

            lines.append("")

        lines.append("---")
        lines.append("")

    return "\n".join(lines)
