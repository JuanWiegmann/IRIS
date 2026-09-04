"""
Fresh Context Validation
========================

Simulates MCP sampling for validation in fresh context.

CURRENT APPROACH (MCP SDK limitation workaround):
Instead of true MCP sampling, we provide a tool that the LLM can call
to validate in a "fresh context" (separate tool call after draft generation).

The LLM workflow:
1. Generate draft (in generation context)
2. Call check_draft_fresh_context(draft) - separate tool call
3. In that NEW context, validate without generation bias
4. Return feedback

This achieves the same goal as MCP sampling would:
- Validation happens in separate context from generation
- No generation bias
- LLM can't "defend" its own work

FUTURE: When MCP SDK adds sampling, replace this with real sampling.
"""

from uuid import UUID
from mcp.types import Tool, TextContent

from src.validation import detect_use_case
from src.tools.check_draft_impl import validate_messaging, validate_coding, validate_mendix
from src.profile import profile_exists
from src.utils import iris_response


# ═══════════════════════════════════════════════════════════
# TOOL: FRESH CONTEXT VALIDATION
# ═══════════════════════════════════════════════════════════

def get_fresh_context_validation_tool() -> Tool:
    """
    Tool for validation in fresh context (Layer 2 simulation).

    Returns:
        MCP Tool specification
    """
    return Tool(
        name="validate_fresh_context",
        description=(
            "Validate a draft in FRESH CONTEXT (Layer 2 validation). "
            "\n\n"
            "**USE CASE:** After generating a draft, call this tool "
            "to validate it WITHOUT generation bias. "
            "\n\n"
            "This is a SEPARATE tool call from generation, so the validation "
            "happens in fresh context. You cannot 'defend' your work - you "
            "judge it objectively."
            "\n\n"
            "**PROTOCOL:**\n"
            "1. Generate draft\n"
            "2. Call validate_fresh_context(draft, context)\n"
            "3. If issues found → revise draft\n"
            "4. Repeat until validation passes\n"
            "5. Show final draft to user"
            "\n\n"
            "**Why this matters:** Fresh context = unbiased validation. "
            "You can't rationalize away issues you'd miss in generation context."
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
                    "description": "Brief description (e.g., 'team email', 'Python function')"
                },
                "original_task": {
                    "type": "string",
                    "description": "Original user request (for context)"
                }
            },
            "required": ["draft", "context"]
        }
    )


async def handle_validate_fresh_context(
    arguments: dict,
    user_id: UUID
) -> list[TextContent]:
    """
    Handle fresh context validation.

    This is called in a SEPARATE context from draft generation,
    providing unbiased validation.

    Args:
        arguments: {"draft": str, "context": str, "original_task": str}
        user_id: User UUID

    Returns:
        Validation result
    """
    # Gate check
    if not profile_exists(user_id):
        return [
            TextContent(
                type="text",
                text=iris_response(
                    "ONBOARDING_REQUIRED\n\n"
                    "No profile found. Complete onboarding first.\n\n"
                    "Call start_onboarding() to begin."
                )
            )
        ]

    draft = arguments["draft"]
    context = arguments.get("context", "")
    original_task = arguments.get("original_task", "")

    if not draft or not draft.strip():
        return [
            TextContent(
                type="text",
                text=iris_response("❌ Error: draft cannot be empty")
            )
        ]

    # Detect use case
    use_case = detect_use_case(context, draft)

    # Route to validator (same as check_draft, but in fresh context)
    from src.validation import UseCase

    if use_case == UseCase.MESSAGING:
        result = await validate_messaging(draft, context, user_id)
    elif use_case == UseCase.CODING:
        result = await validate_coding(draft, context, user_id)
    elif use_case == UseCase.MENDIX:
        result = await validate_mendix(draft, context, user_id)
    else:
        result = await validate_messaging(draft, context, user_id)

    # Format response
    response = result.format_for_llm()

    # Add Layer 2 marker
    response = "**[Layer 2: Fresh Context Validation]**\n\n" + response

    if original_task:
        response += f"\n\n*Original task: {original_task}*"

    return [
        TextContent(
            type="text",
            text=iris_response(response)
        )
    ]


# ═══════════════════════════════════════════════════════════
# FUTURE: TRUE MCP SAMPLING
# ═══════════════════════════════════════════════════════════

"""
When MCP SDK adds sampling support, replace the above with:

from mcp.server.sampling import create_message, SamplingRequest

async def request_validation_via_sampling(
    draft: str,
    context: str,
    user_id: UUID
) -> ValidationResult:
    # Create validation prompt
    prompt = build_validation_prompt(draft, context, user_id)

    # Request sampling from user's LLM
    sampling_request = SamplingRequest(
        messages=[create_message(role="user", content=prompt)],
        modelPreferences=["haiku", "sonnet"],
        maxTokens=500,
        temperature=0.0
    )

    response = await app.request_sampling(sampling_request)

    # Parse and return
    return parse_validation_response(response.content)

This will provide TRUE fresh-context validation via MCP protocol.
"""
