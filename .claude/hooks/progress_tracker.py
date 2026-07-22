"""
Progress Tracker Hook (PostToolUse)

Fires after Edit/Write on CLAUDE.md (when segment checkboxes change).
Detects segment completion and signals that ARCHITECTURE.md should be updated.

This hook is lightweight — it only triggers a reminder when it detects
a segment checkbox changing from [ ] to [x] in the root CLAUDE.md.
"""

import json
import sys


def main():
    try:
        input_data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        json.dump({"continue": True}, sys.stdout)
        return

    tool_input = input_data.get("tool_input", {})
    file_path = tool_input.get("file_path", "")
    new_content = tool_input.get("new_string", "") or tool_input.get("content", "")

    # Only care about changes to the root CLAUDE.md
    normalized = file_path.replace("\\", "/")
    if not normalized.endswith("CLAUDE.md") or "src/" in normalized or "learning/" in normalized:
        json.dump({"continue": True}, sys.stdout)
        return

    # Check if a segment was just marked complete
    if "[x] Segment" in new_content or "[X] Segment" in new_content:
        output = {
            "continue": True,
            "hookSpecificOutput": {
                "hookEventName": "PostToolUse",
                "additionalContext": (
                    "Segment completed! Update ARCHITECTURE.md to reflect the new state. "
                    "Move the 'current' marker to the next segment in the Mermaid diagram."
                )
            }
        }
    else:
        output = {"continue": True}

    json.dump(output, sys.stdout)


if __name__ == "__main__":
    main()
