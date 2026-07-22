"""
Pre-flight Explainer Hook (PreToolUse)

Fires BEFORE Edit, Write, or Read executes.
Outputs one sentence explaining the TARGET of the operation — why we're doing this.
"""

import json
import sys
from pathlib import Path


# Map file paths to their purpose in KIM's architecture
PATH_PURPOSE = {
    "src/server": "MCP server entry point — how KIM exposes itself to LLMs",
    "src/tools/": "MCP tools — the interface LLMs call into",
    "src/tools/context": "get_context tool — providing profile + relevant examples to the LLM",
    "src/tools/check_draft": "check_draft tool — blind validation of LLM output against profile",
    "src/tools/onboarding": "onboarding tools — target-based preference elicitation",
    "src/tools/log_output": "log_output tool — storing user outputs for future retrieval",
    "src/profile/": "user profile — the structured representation of who the user is",
    "src/retrieval/": "retrieval engine — finding relevant past outputs for the current query",
    "src/validation/": "validation logic — deterministic rules that check drafts against profile",
    "src/onboarding/": "GATE onboarding — targets, barriers, state machine for preference learning",
    "src/anleitung/": "Anleitung — protocol instructions that guide the LLM's behavior",
    "src/orchestration/": "Layer 2 — MCP sampling orchestration for advanced clients",
    "src/data/": "data layer — persistence for outputs, memory, vectors",
    "src/observability/": "observability — logging, metrics, tracing",
    "config/": "configuration — server settings, data paths",
    "tests/unit/": "unit test — verifying one component in isolation",
    "tests/integration/": "integration test — verifying the full MCP flow end-to-end",
    "learning/": "learning material — certification teaching content",
    "docs/": "documentation — diagrams, research notes, checklists",
    "prompts/": "prompt templates — versioned instructions for LLMs",
    ".claude/hooks/": "Claude Code hook — automatic behavior on events",
    ".claude/skills/": "Claude Code skill — on-demand workflow",
    "CLAUDE.md": "project constitution — loaded every session automatically",
    "ARCHITECTURE.md": "architecture diagram — visual system state with build progress",
}


def get_purpose(file_path: str) -> str:
    """Find the most specific purpose match for a file path."""
    normalized = file_path.replace("\\", "/")
    best_match = ""
    best_length = 0
    for prefix, purpose in PATH_PURPOSE.items():
        if prefix in normalized and len(prefix) > best_length:
            best_match = purpose
            best_length = len(prefix)
    return best_match


def main():
    try:
        input_data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        json.dump({"continue": True}, sys.stdout)
        return

    tool_input = input_data.get("tool_input", {})
    tool_name = input_data.get("tool_name", "")
    file_path = tool_input.get("file_path", "")

    # Build the one-sentence explanation based on tool type
    msg = ""

    if tool_name in ("Read", "Write", "Edit"):
        if not file_path or ".claude/plans" in file_path or ".claude/projects" in file_path:
            json.dump({"continue": True}, sys.stdout)
            return
        filename = Path(file_path).name
        purpose = get_purpose(file_path)
        action = {"Read": "Reading", "Write": "Creating", "Edit": "Modifying"}[tool_name]
        msg = f"{action} `{filename}`" + (f" — {purpose}" if purpose else "")

    elif tool_name == "Bash":
        command = tool_input.get("command", "")
        if command:
            short_cmd = command[:80] + ("..." if len(command) > 80 else "")
            msg = f"Running: {short_cmd}"

    elif tool_name == "Glob":
        pattern = tool_input.get("pattern", "")
        msg = f"Searching files: {pattern}"

    elif tool_name == "Grep":
        pattern = tool_input.get("pattern", "")
        msg = f"Searching content: {pattern}"

    elif tool_name == "Agent":
        description = tool_input.get("description", "") or tool_input.get("prompt", "")[:60]
        msg = f"Spawning agent: {description}"

    elif tool_name == "Workflow":
        msg = "Running workflow orchestration"

    elif tool_name == "Skill":
        skill = tool_input.get("skill", "")
        msg = f"Invoking skill: /{skill}"

    elif tool_name == "TaskCreate":
        msg = "Creating task for progress tracking"

    elif tool_name == "TaskUpdate":
        msg = "Updating task status"

    elif tool_name == "WebFetch":
        url = tool_input.get("url", "")
        msg = f"Fetching: {url[:60]}"

    else:
        msg = f"Tool: {tool_name}"

    if not msg:
        json.dump({"continue": True}, sys.stdout)
        return

    output = {
        "continue": True,
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "additionalContext": f"| PRE-INFO: {msg} |"
        }
    }
    json.dump(output, sys.stdout)


if __name__ == "__main__":
    main()
