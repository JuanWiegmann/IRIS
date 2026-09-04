"""
Check Draft Tool (Complete)
===========================

MCP tool for validating drafts with use-case-aware routing.

Validation Strategy:
1. Detect use case (messaging/coding/Mendix)
2. Apply deterministic checks (per use case)
3. Apply MCP sampling for semantic validation (if available)
4. Combine results and return feedback

Use Cases:
- MESSAGING: tone, format, boundaries
- CODING: syntax patterns, best practices (+ Ponytail if available)
- MENDIX: domain rules, XML structure (no CLI execution)
"""

from uuid import UUID
from mcp.types import Tool, TextContent

from src.validation import detect_use_case, UseCase
from src.tools.check_draft_impl import validate_messaging, validate_coding, validate_mendix
from src.profile import profile_exists
from src.utils import iris_response


# ═══════════════════════════════════════════════════════════
# TOOL DEFINITION
# ═══════════════════════════════════════════════════════════

def get_check_draft_tool() -> Tool:
    """
    Get check_draft tool definition for MCP.

    Returns:
        MCP Tool specification
    """
    return Tool(
        name="check_draft",
        description=(
            "Validate a draft against the user's profile and use-case-specific rules. "
            "\n\n"
            "This performs two-stage validation:\n"
            "1. Deterministic checks (style, format, patterns)\n"
            "2. Semantic validation (via MCP sampling if available)\n"
            "\n"
            "Automatically detects use case:\n"
            "- MESSAGING: emails, documents (checks tone, format, boundaries)\n"
            "- CODING: code validation (syntax, best practices, Ponytail if available)\n"
            "- MENDIX: Mendix validation (domain rules, XML structure)\n"
            "\n"
            "Call this BEFORE showing a draft to the user to catch issues early."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "draft": {
                    "type": "string",
                    "description": "The draft content to validate"
                },
                "context": {
                    "type": "string",
                    "description": "Brief description of what this draft is (e.g., 'team email', 'Python function', 'Mendix entity')"
                }
            },
            "required": ["draft", "context"]
        }
    )


# ═══════════════════════════════════════════════════════════
# TOOL HANDLER
# ═══════════════════════════════════════════════════════════

async def handle_check_draft(arguments: dict, user_id: UUID) -> list[TextContent]:
    """
    Handle check_draft tool call.

    Args:
        arguments: {"draft": str, "context": str}
        user_id: User UUID

    Returns:
        List with one TextContent containing validation results
    """
    # ═══ GATE CHECK: Profile must exist ═══
    # Learning: learning/07_user_profiles/README.md#onboarding-gates
    if not profile_exists(user_id):
        return [
            TextContent(
                type="text",
                text=iris_response(
                    "ONBOARDING_REQUIRED\n\n"
                    "No profile found. You must complete onboarding before using check_draft.\n\n"
                    "Call start_onboarding() to begin."
                )
            )
        ]

    draft = arguments["draft"]
    context = arguments.get("context", "")

    if not draft or not draft.strip():
        return [
            TextContent(
                type="text",
                text=iris_response("❌ Error: draft cannot be empty")
            )
        ]

    # ═══ STEP 1: Detect Use Case ═══
    use_case = detect_use_case(context, draft)

    # ═══ STEP 2: Route to Appropriate Validator ═══
    if use_case == UseCase.MESSAGING:
        result = await validate_messaging(draft, context, user_id)
    elif use_case == UseCase.CODING:
        result = await validate_coding(draft, context, user_id)
    elif use_case == UseCase.MENDIX:
        result = await validate_mendix(draft, context, user_id)
    else:
        result = await validate_messaging(draft, context, user_id)  # Fallback

    # Format result for LLM
    return [
        TextContent(
            type="text",
            text=iris_response(result.format_for_llm())
        )
    ]
