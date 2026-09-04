"""
Project Context Tracking
========================

Automatically tracks project progress and major changes during conversations.

Flow:
1. LLM detects when major project information surfaces
2. LLM calls: update_project_context(project, update, context)
3. IRIS stores update with timestamp
4. User can query: "What's the latest on project X?"
5. IRIS returns recent updates for that project

Design: Continuous project memory - user doesn't need to manually track progress.
"""

from pathlib import Path
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any
from mcp.types import Tool, TextContent


# ═══════════════════════════════════════════════════════════
# PROJECT DETECTION SIGNALS
# ═══════════════════════════════════════════════════════════

PROJECT_UPDATE_SIGNALS = {
    "major_change": {
        "description": "Significant project change or milestone",
        "triggers": [
            "User reports completing a feature",
            "User mentions a bug was fixed",
            "User describes a refactoring",
            "User mentions a deployment",
            "User reports a test passing/failing",
            "Architecture decision made"
        ],
        "should_log": True
    },
    "context_shift": {
        "description": "Change in project focus or priorities",
        "triggers": [
            "User switches from feature A to feature B",
            "User mentions deadline change",
            "User reports blocker removed/added",
            "Scope change mentioned"
        ],
        "should_log": True
    },
    "technical_detail": {
        "description": "Important technical information about project",
        "triggers": [
            "User explains architecture pattern used",
            "User mentions tech stack choice",
            "User describes data model",
            "User mentions integration points"
        ],
        "should_log": True
    },
    "status_update": {
        "description": "Current status of work",
        "triggers": [
            "User mentions percentage complete",
            "User describes what's blocked",
            "User mentions what's next",
            "User reports timeline"
        ],
        "should_log": True
    },
    "collaboration": {
        "description": "Team/stakeholder information",
        "triggers": [
            "User mentions who's working on what",
            "User mentions stakeholder feedback",
            "User mentions team decision"
        ],
        "should_log": True
    }
}


# ═══════════════════════════════════════════════════════════
# STORAGE
# ═══════════════════════════════════════════════════════════

def get_project_updates_path(user_id: str) -> Path:
    """Get path to user's project updates log."""
    iris_root = Path.home() / ".iris"
    projects_dir = iris_root / "data" / "projects"
    projects_dir.mkdir(parents=True, exist_ok=True)
    return projects_dir / f"{user_id}_project_updates.json"


def load_project_updates(user_id: str) -> Dict[str, List[Dict]]:
    """
    Load all project updates for user.

    Returns:
        {
            "project_name": [
                {
                    "timestamp": "2026-09-04T16:00:00Z",
                    "update": "Completed user authentication feature",
                    "context": "Added JWT tokens, password hashing",
                    "update_type": "major_change"
                },
                ...
            ],
            ...
        }
    """
    path = get_project_updates_path(user_id)
    if not path.exists():
        return {}

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_project_update(
    user_id: str,
    project: str,
    update: str,
    context: str,
    update_type: str
):
    """Save a project update."""
    all_updates = load_project_updates(user_id)

    if project not in all_updates:
        all_updates[project] = []

    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "update": update,
        "context": context,
        "update_type": update_type
    }

    all_updates[project].append(entry)

    path = get_project_updates_path(user_id)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(all_updates, f, indent=2)


def get_recent_updates(
    user_id: str,
    project: str = None,
    days: int = 7
) -> List[Dict]:
    """
    Get recent project updates.

    Args:
        user_id: User identifier
        project: Specific project name (None = all projects)
        days: How many days back to look

    Returns:
        List of recent updates, newest first
    """
    all_updates = load_project_updates(user_id)

    cutoff = datetime.utcnow() - timedelta(days=days)
    recent = []

    if project:
        # Single project
        if project in all_updates:
            for update in all_updates[project]:
                timestamp = datetime.fromisoformat(update["timestamp"])
                if timestamp >= cutoff:
                    recent.append({
                        "project": project,
                        **update
                    })
    else:
        # All projects
        for proj_name, updates in all_updates.items():
            for update in updates:
                timestamp = datetime.fromisoformat(update["timestamp"])
                if timestamp >= cutoff:
                    recent.append({
                        "project": proj_name,
                        **update
                    })

    # Sort by timestamp, newest first
    recent.sort(key=lambda x: x["timestamp"], reverse=True)
    return recent


# ═══════════════════════════════════════════════════════════
# PROFILE INTEGRATION
# ═══════════════════════════════════════════════════════════

async def update_profile_projects(user_id: str):
    """
    Update user profile's "current_projects" field based on recent activity.

    Looks at last 30 days of updates and updates profile accordingly.
    """
    from src.profile import get_or_create_profile

    # Get recent updates across all projects
    all_updates = load_project_updates(user_id)
    cutoff = datetime.utcnow() - timedelta(days=30)

    active_projects = []
    for proj_name, updates in all_updates.items():
        # Check if this project has recent activity
        recent_activity = [
            u for u in updates
            if datetime.fromisoformat(u["timestamp"]) >= cutoff
        ]

        if recent_activity:
            # Get latest update for summary
            latest = recent_activity[-1]
            active_projects.append({
                "name": proj_name,
                "latest_update": latest["update"],
                "last_activity": latest["timestamp"]
            })

    # Load and update profile
    profile = await get_or_create_profile(user_id)
    if profile:
        # Update current_projects field
        profile.current_projects = [p["name"] for p in active_projects]

        # Save (convert UUID to string)
        profile_path = Path.home() / ".iris" / "data" / "profiles" / f"{profile.id}.json"
        profile_data = profile.model_dump()
        profile_data["id"] = str(profile_data["id"])  # UUID to string

        with open(profile_path, "w", encoding="utf-8") as f:
            json.dump(profile_data, f, indent=2)


# ═══════════════════════════════════════════════════════════
# TOOLS
# ═══════════════════════════════════════════════════════════

def get_update_project_context_tool() -> Tool:
    """Tool for logging project updates."""
    return Tool(
        name="update_project_context",
        description=(
            "Log important project updates and changes automatically. "
            "\n\n"
            "Use when the user mentions:"
            "- Completing a feature or milestone"
            "- Fixing a bug or issue"
            "- Making an architecture decision"
            "- Changing project focus or priorities"
            "- Important technical details about the project"
            "- Status updates (what's done, what's blocked, what's next)"
            "\n\n"
            "This builds a timeline of project progress that the user can query later."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "project": {
                    "type": "string",
                    "description": "Project name (e.g., 'Plantafel', 'IRIS', 'Ringline')"
                },
                "update": {
                    "type": "string",
                    "description": "Brief summary of what changed (1-2 sentences)"
                },
                "context": {
                    "type": "string",
                    "description": "Additional context or details"
                },
                "update_type": {
                    "type": "string",
                    "description": "Type of update",
                    "enum": ["major_change", "context_shift", "technical_detail", "status_update", "collaboration"]
                }
            },
            "required": ["project", "update", "context", "update_type"]
        }
    )


def get_query_project_context_tool() -> Tool:
    """Tool for querying project history."""
    return Tool(
        name="query_project_context",
        description=(
            "Retrieve recent updates for a project. "
            "\n\n"
            "Use when the user asks:"
            "- \"What's the latest on project X?\""
            "- \"Where did we leave off on X?\""
            "- \"What have I done on X recently?\""
            "- \"Show me the history of X\""
            "\n\n"
            "Returns timeline of recent changes."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "project": {
                    "type": "string",
                    "description": "Project name (optional - if omitted, returns all projects)"
                },
                "days": {
                    "type": "integer",
                    "description": "How many days back to look (default: 7)",
                    "minimum": 1,
                    "maximum": 90
                }
            },
            "required": []
        }
    )


def get_project_detection_signals_tool() -> Tool:
    """Tool for getting project update detection patterns."""
    return Tool(
        name="get_project_signals",
        description=(
            "Get signals and patterns for detecting when to log project updates. "
            "\n\n"
            "Call this at the start of analyzing user messages to understand "
            "what kinds of project information should be logged."
        ),
        inputSchema={
            "type": "object",
            "properties": {},
            "required": []
        }
    )


# ═══════════════════════════════════════════════════════════
# HANDLERS
# ═══════════════════════════════════════════════════════════

async def handle_update_project_context(arguments: dict, user_id: str) -> list[TextContent]:
    """Handle project update logging."""
    from src.utils import iris_response

    project = arguments.get("project")
    update = arguments.get("update")
    context = arguments.get("context", "")
    update_type = arguments.get("update_type", "status_update")

    # Save update
    save_project_update(user_id, project, update, context, update_type)

    # Update profile's current_projects field
    await update_profile_projects(user_id)

    response = f"""**Project update logged**

Project: {project}
Update: {update}
Type: {update_type}

This is now part of your project timeline and will appear when you query "{project}" history.
"""

    return [TextContent(type="text", text=iris_response(response))]


async def handle_query_project_context(arguments: dict, user_id: str) -> list[TextContent]:
    """Handle project history query."""
    from src.utils import iris_response

    project = arguments.get("project")
    days = arguments.get("days", 7)

    # Get recent updates
    recent = get_recent_updates(user_id, project, days)

    if not recent:
        if project:
            response = f"No updates found for project '{project}' in the last {days} days."
        else:
            response = f"No project updates found in the last {days} days."
    else:
        if project:
            response = f"# Recent Updates: {project}\n\n"
        else:
            response = f"# All Project Updates (last {days} days)\n\n"

        # Group by project if showing all
        if not project:
            by_project = {}
            for update in recent:
                proj = update["project"]
                if proj not in by_project:
                    by_project[proj] = []
                by_project[proj].append(update)

            for proj, updates in by_project.items():
                response += f"## {proj}\n\n"
                for upd in updates:
                    timestamp = datetime.fromisoformat(upd["timestamp"])
                    date_str = timestamp.strftime("%Y-%m-%d %H:%M")
                    response += f"**{date_str}** — {upd['update']}\n"
                    if upd["context"]:
                        response += f"  ↳ {upd['context']}\n"
                    response += "\n"
        else:
            for upd in recent:
                timestamp = datetime.fromisoformat(upd["timestamp"])
                date_str = timestamp.strftime("%Y-%m-%d %H:%M")
                response += f"**{date_str}** — {upd['update']}\n"
                if upd["context"]:
                    response += f"  ↳ {upd['context']}\n"
                response += f"  *Type: {upd['update_type']}*\n\n"

    return [TextContent(type="text", text=iris_response(response))]


async def handle_get_project_signals(arguments: dict) -> list[TextContent]:
    """Return project detection signals."""
    import json
    from src.utils import iris_response

    response = {
        "signals": PROJECT_UPDATE_SIGNALS,
        "auto_detect": "Call get_project_signals() when analyzing user messages to understand what to log",
        "workflow": {
            "step_1": "Check if user message contains project information",
            "step_2": "Match against signal patterns",
            "step_3": "If match found → call update_project_context()",
            "step_4": "Continue with normal response"
        }
    }

    return [TextContent(
        type="text",
        text=iris_response(json.dumps(response, indent=2))
    )]
