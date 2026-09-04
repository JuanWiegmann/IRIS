"""
IRIS MCP Server
==============

Entry point for the IRIS MCP middleware server.

This server exposes tools that allow any LLM to access personalized context,
validate drafts, manage onboarding, and log outputs.

Architecture:
- No internal LLM (user's LLM does all reasoning)
- Pure logic + data (deterministic validation, retrieval)
- Research-backed (GATE, Wu et al. 2024)
"""

import asyncio
from typing import Any
from uuid import UUID

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, Resource, Prompt, PromptMessage

from src.observability import setup_logging, get_logger, log_tool_call
from src.anleitung import get_anleitung
from src.utils import get_user_id, iris_response

from src.profile import get_or_create_profile, format_profile_for_llm, profile_exists
from src.retrieval.hybrid import retrieve_relevant_outputs, format_outputs_for_llm
from src.tools.log_output import get_log_output_tool, handle_log_output
from src.tools.check_draft import get_check_draft_tool, handle_check_draft
from src.tools.feedback_categories import (
    get_feedback_categories_tool,
    get_apply_feedback_change_tool,
    handle_get_feedback_categories,
    handle_apply_feedback_change
)
from src.tools.project_context import (
    get_update_project_context_tool,
    get_query_project_context_tool,
    get_project_detection_signals_tool,
    handle_update_project_context,
    handle_query_project_context,
    handle_get_project_signals
)
from src.orchestration.fresh_context_validation import (
    get_fresh_context_validation_tool,
    handle_validate_fresh_context
)
from src.memory import (
    get_recent_messages,
    format_stm_for_llm,
    get_summaries,
    format_summaries_for_llm,
    get_ltm_context,
    format_ltm_for_llm
)
from src.tools.onboarding import (
    start_onboarding,
    store_answer,
    get_next_question,
    complete_onboarding,
)


# ═══════════════════════════════════════════════════════════
# LOGGING SETUP
# ═══════════════════════════════════════════════════════════

setup_logging()
logger = get_logger("server")


# ═══════════════════════════════════════════════════════════
# SERVER INSTANCE
# ═══════════════════════════════════════════════════════════

app = Server("iris-server")


# ═══════════════════════════════════════════════════════════
# RESOURCES: Protocol Instructions
# ═══════════════════════════════════════════════════════════

@app.list_resources()
async def list_resources() -> list[Resource]:
    """
    Register MCP resources.

    Resources are static content that LLMs can read (like protocol instructions).
    """
    return [
        Resource(
            uri="iris://protocol",
            name="IRIS Protocol (Anleitung)",
            mimeType="text/markdown",
            description="Strict protocol for using IRIS. MUST be followed by all LLMs."
        )
    ]


@app.read_resource()
async def read_resource(uri: str) -> str:
    """
    Read a resource by URI.

    Args:
        uri: Resource URI (e.g., "iris://protocol")

    Returns:
        Resource content as string
    """
    if uri == "iris://protocol":
        return get_anleitung()

    raise ValueError(f"Unknown resource: {uri}")


# ═══════════════════════════════════════════════════════════
# PROMPTS: Auto-loaded Protocol
# ═══════════════════════════════════════════════════════════

@app.list_prompts()
async def list_prompts() -> list[Prompt]:
    """
    Register MCP prompts.

    Prompts are auto-loaded into the LLM's context.
    This is how we enforce the profile-first protocol.
    """
    return [
        Prompt(
            name="iris-protocol",
            description="IRIS usage protocol - MANDATORY. Enforces profile-first workflow.",
            arguments=[]
        )
    ]


@app.get_prompt()
async def get_prompt(name: str, arguments: dict) -> list[PromptMessage]:
    """
    Get a prompt by name.

    Args:
        name: Prompt name
        arguments: Prompt arguments (unused for iris-protocol)

    Returns:
        List of messages to inject into context
    """
    if name == "iris-protocol":
        return [
            PromptMessage(
                role="user",
                content=TextContent(
                    type="text",
                    text=get_anleitung()
                )
            )
        ]

    raise ValueError(f"Unknown prompt: {name}")


# ═══════════════════════════════════════════════════════════
# TOOL: get_context
# ═══════════════════════════════════════════════════════════

@app.list_tools()
async def list_tools() -> list[Tool]:
    """
    Register all available tools.

    This is called by MCP clients to discover what tools are available.
    """
    # Learning: learning/01_mcp_tools/README.md#tool-registration
    return [
        Tool(
            name="get_context",
            description=(
                "Retrieve personalized context for the user. "
                "Returns the user's profile (tone, style, format preferences) "
                "and relevant past outputs (ranked by relevance). "
                "\n\n"
                "Use this when you need to know HOW to present information "
                "to this specific user."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The current query or task description (used for ranking relevant outputs)"
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="start_onboarding",
            description=(
                "Start onboarding flow to learn user preferences. "
                "This is a 10-question adaptive flow (~5 minutes) based on GATE research. "
                "\n\n"
                "The flow starts with 2 anchor questions (role + AI usage), then adapts "
                "to ask the most relevant questions based on user's profile type. "
                "\n\n"
                "Returns the first question to ask."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "User identifier"
                    }
                },
                "required": ["user_id"]
            }
        ),
        Tool(
            name="store_answer",
            description=(
                "Store user's answer to an onboarding question. "
                "\n\n"
                "After storing, returns validation result and next question (if any). "
                "\n\n"
                "Research: GATE methodology - edge-case questions reveal tacit preferences."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "User identifier"
                    },
                    "target_id": {
                        "type": "string",
                        "description": "Target dimension ID (e.g., 'role', 'technical_depth')"
                    },
                    "answer": {
                        "type": "object",
                        "description": "User's answer. Format: binary/edge-case use {chosen_option: 'value'}, open questions use {answer: 'text'}",
                        "properties": {
                            "chosen_option": {
                                "type": "string",
                                "description": "For binary/edge-case questions: the chosen option value"
                            },
                            "answer": {
                                "type": "string",
                                "description": "For open questions: free-text answer"
                            }
                        }
                    }
                },
                "required": ["user_id", "target_id", "answer"]
            }
        ),
        Tool(
            name="get_next_question",
            description=(
                "Get next onboarding question for the user. "
                "\n\n"
                "Returns question details with research-backed guidance on how to ask it. "
                "Returns null if onboarding is complete."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "User identifier"
                    }
                },
                "required": ["user_id"]
            }
        ),
        Tool(
            name="complete_onboarding",
            description=(
                "Complete onboarding and generate user profile. "
                "\n\n"
                "Can only be called when core questions (80% minimum) are answered. "
                "Generates UserProfile from collected evidence."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "User identifier"
                    }
                },
                "required": ["user_id"]
            }
        ),
        get_log_output_tool(),
        get_check_draft_tool(),
        get_feedback_categories_tool(),
        get_apply_feedback_change_tool(),
        get_update_project_context_tool(),
        get_query_project_context_tool(),
        get_project_detection_signals_tool(),
        get_fresh_context_validation_tool()
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """
    Execute a tool based on its name.

    Args:
        name: Tool name (e.g., "get_context")
        arguments: Tool arguments as a dict

    Returns:
        List of text content blocks
    """
    # Log the tool call
    log_tool_call(logger, name, arguments)

    if name == "get_context":
        return await handle_get_context(arguments)

    if name == "log_output":
        user_id = get_user_id()
        return await handle_log_output(arguments, user_id)

    if name == "check_draft":
        user_id = get_user_id()
        return await handle_check_draft(arguments, user_id)

    if name == "get_feedback_categories":
        return await handle_get_feedback_categories(arguments)

    if name == "apply_feedback_change":
        user_id = get_user_id()
        return await handle_apply_feedback_change(arguments, user_id)

    if name == "update_project_context":
        user_id = get_user_id()
        return await handle_update_project_context(arguments, user_id)

    if name == "query_project_context":
        user_id = get_user_id()
        return await handle_query_project_context(arguments, user_id)

    if name == "get_project_signals":
        return await handle_get_project_signals(arguments)

    if name == "validate_fresh_context":
        user_id = get_user_id()
        return await handle_validate_fresh_context(arguments, user_id)

    # Onboarding tools
    # Learning: learning/07_user_profiles/README.md#gate-methodology
    if name == "start_onboarding":
        return await handle_start_onboarding(arguments)

    if name == "store_answer":
        return await handle_store_answer(arguments)

    if name == "get_next_question":
        return await handle_get_next_question(arguments)

    if name == "complete_onboarding":
        return await handle_complete_onboarding(arguments)

    raise ValueError(f"Unknown tool: {name}")


async def handle_get_context(arguments: dict) -> list[TextContent]:
    """
    Handle get_context tool call.

    Loads user profile and returns personalized context.

    Segment 2: Loads real profile data
    Segment 3: Will add relevant past outputs (retrieval + ranking)

    Args:
        arguments: {"query": str}

    Returns:
        List with one TextContent block containing the context
    """
    query = arguments.get("query", "")

    # Get current system user's ID
    user_id = get_user_id()

    # ═══ GATE CHECK: Profile must exist ═══
    # Learning: learning/07_user_profiles/README.md#onboarding-gates
    if not profile_exists(user_id):
        return [
            TextContent(
                type="text",
                text=iris_response(
                    "ONBOARDING_REQUIRED\n\n"
                    "No profile found. You must complete onboarding before using IRIS.\n\n"
                    "Call start_onboarding() to begin. This takes ~5 minutes and enables full personalization."
                )
            )
        ]

    # Load user profile (Segment 2)
    # Learning: learning/02_data_modeling/README.md#profile-loading
    profile = await get_or_create_profile(user_id)

    # Block if no profile exists (onboarding required)
    if profile is None:
        return [
            types.TextContent(
                type="text",
                text="ONBOARDING_REQUIRED\n\nNo profile found. You must complete onboarding before using get_context.\n\nCall start_onboarding() to begin."
            )
        ]

    # Format profile as markdown for LLM
    profile_text = format_profile_for_llm(profile)

    # Retrieve relevant past outputs (Segment 3)
    # Learning: learning/06_memory/README.md#hybrid-retrieval
    try:
        relevant_outputs = await retrieve_relevant_outputs(
            user_id=user_id,
            query=query,
            top_k=5
        )
        outputs_text = format_outputs_for_llm(relevant_outputs)
    except Exception:
        # No outputs yet, or retrieval failed
        outputs_text = "*(No past outputs stored yet)*"

    # ═══ MEMORY TIERS (Westhaeusser et al. 2024) ═══

    # STM: Recent conversation
    try:
        stm_messages = get_recent_messages(user_id, limit=10)
        stm_text = format_stm_for_llm(stm_messages)
    except Exception:
        stm_text = "*(No recent conversation)*"

    # Summaries: Conversation history
    try:
        summaries = get_summaries(user_id, limit=3)
        summaries_text = format_summaries_for_llm(summaries)
    except Exception:
        summaries_text = "*(No conversation history)*"

    # LTM: Project memory (reuses project_context)
    try:
        ltm_updates = await get_ltm_context(user_id, days=30)
        ltm_text = format_ltm_for_llm(ltm_updates)
    except Exception:
        ltm_text = "*(No project memory)*"

    # Build full context response
    response = f"""# Personalized Context for: "{query}"

{profile_text}

## Recent Conversation (STM)
{stm_text}

## Relevant Past Outputs
{outputs_text}

## Conversation History (Summaries)
{summaries_text}

## Project Memory (LTM)
{ltm_text}

---
*Profile: ~/.iris/data/profiles/{profile.id}.json*
*Retrieval: Hybrid BM25 + vector similarity (Wu et al. 2024)*
*Memory: Multi-tiered (Westhaeusser et al. 2024)*
"""

    return [
        TextContent(
            type="text",
            text=iris_response(response)
        )
    ]


# ═══════════════════════════════════════════════════════════
# ONBOARDING TOOL HANDLERS
# ═══════════════════════════════════════════════════════════

async def handle_start_onboarding(arguments: dict) -> list[TextContent]:
    """Handle start_onboarding tool call."""
    import json
    from src.utils import get_system_user

    # Use system username (ignore any user_id passed by LLM)
    user_id = get_system_user()
    result = start_onboarding(user_id)

    return [
        TextContent(
            type="text",
            text=iris_response(json.dumps(result, indent=2))
        )
    ]


async def handle_store_answer(arguments: dict) -> list[TextContent]:
    """Handle store_answer tool call."""
    import json
    from src.utils import get_system_user

    # Use system username (ignore any user_id passed by LLM)
    user_id = get_system_user()
    target_id = arguments.get("target_id")
    answer = arguments.get("answer", {})

    result = store_answer(user_id, target_id, answer)

    return [
        TextContent(
            type="text",
            text=iris_response(json.dumps(result, indent=2))
        )
    ]


async def handle_get_next_question(arguments: dict) -> list[TextContent]:
    """Handle get_next_question tool call."""
    import json
    from src.utils import get_system_user

    # Use system username (ignore any user_id passed by LLM)
    user_id = get_system_user()
    result = get_next_question(user_id)

    if result is None:
        result = {"status": "complete", "message": "Onboarding complete"}

    return [
        TextContent(
            type="text",
            text=iris_response(json.dumps(result, indent=2))
        )
    ]


async def handle_complete_onboarding(arguments: dict) -> list[TextContent]:
    """Handle complete_onboarding tool call."""
    import json
    from src.utils import get_system_user

    # Use system username (ignore any user_id passed by LLM)
    user_id = get_system_user()
    result = complete_onboarding(user_id)

    return [
        TextContent(
            type="text",
            text=iris_response(json.dumps(result, indent=2))
        )
    ]


# ═══════════════════════════════════════════════════════════
# SERVER ENTRY POINT
# ═══════════════════════════════════════════════════════════

async def run_server():
    """
    Start the MCP server via stdio transport.

    The server communicates with the LLM client via stdin/stdout
    using the MCP protocol (JSON-RPC 2.0).
    """
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


def main():
    """Console script entry point (synchronous)."""
    asyncio.run(run_server())


if __name__ == "__main__":
    main()
