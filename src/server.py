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

from src.profile import get_or_create_profile, format_profile_for_llm, profile_exists
from src.retrieval.hybrid import retrieve_relevant_outputs, format_outputs_for_llm
from src.tools.log_output import get_log_output_tool, handle_log_output
from src.tools.check_draft import get_check_draft_tool, handle_check_draft
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
        get_check_draft_tool()
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
        # TODO: Get user_id from MCP session context
        from uuid import uuid5, NAMESPACE_DNS
        demo_user_id = uuid5(NAMESPACE_DNS, "iris.user.demo_user")
        return await handle_log_output(arguments, demo_user_id)

    if name == "check_draft":
        # TODO: Get user_id from MCP session context
        from uuid import uuid5, NAMESPACE_DNS
        demo_user_id = uuid5(NAMESPACE_DNS, "iris.user.demo_user")
        return await handle_check_draft(arguments, demo_user_id)

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
    from uuid import uuid5, NAMESPACE_DNS

    query = arguments.get("query", "")

    # TODO: Get user_id from MCP session context
    # For now, use a fixed demo user ID
    # Generate consistent UUID from user_id string (same as profile_generation.py)
    user_id_str = "demo_user"
    demo_user_id = uuid5(NAMESPACE_DNS, f"iris.user.{user_id_str}")

    # ═══ GATE CHECK: Profile must exist ═══
    # Learning: learning/07_user_profiles/README.md#onboarding-gates
    if not profile_exists(demo_user_id):
        return [
            TextContent(
                type="text",
                text="ONBOARDING_REQUIRED\n\n"
                     "No profile found. You must complete onboarding before using IRIS.\n\n"
                     "Call start_onboarding() to begin. This takes ~5 minutes and enables full personalization."
            )
        ]

    # Load or create user profile (Segment 2)
    # Learning: learning/02_data_modeling/README.md#profile-loading
    profile = await get_or_create_profile(demo_user_id)

    # Format profile as markdown for LLM
    profile_text = format_profile_for_llm(profile)

    # Retrieve relevant past outputs (Segment 3)
    # Learning: learning/06_memory/README.md#hybrid-retrieval
    try:
        relevant_outputs = await retrieve_relevant_outputs(
            user_id=demo_user_id,
            query=query,
            top_k=5
        )
        outputs_text = format_outputs_for_llm(relevant_outputs)
    except Exception:
        # No outputs yet, or retrieval failed
        outputs_text = "*(No past outputs stored yet)*"

    # Build full context response with Janus visual
    janus_header = """
    ┌─────────────────────────────────────┐
    │      JANUS                   │
    │                                     │
    │  PAST ◀───          ───▶ PRESENT   │
    │    ___                ___           │
    │   /• •\\              /• •\\          │
    │  ( ←_• )            ( •_→ )         │
    │   \\___/              \\___/          │
    │    |▓|                |▓|           │
    │   /═╬═\\              /═╬═\\          │
    │  ( ▓▓▓ )            ( ▓▓▓ )         │
    │   |║║|               |║║|          │
    │   | | |              | | |         │
    │  /  |  \\            /  |  \\        │
    │                                     │
    │  [Context served from both sides]   │
    └─────────────────────────────────────┘
    """

    response = f"""{janus_header}

# Personalized Context for: "{query}"

{profile_text}

## Relevant Past Outputs
{outputs_text}

---
*Served by Janus • Profile: ~/.iris/profiles/{profile.id}.json*
*Retrieval: Hybrid BM25 + vector similarity (Wu et al. 2024)*
"""

    return [
        TextContent(
            type="text",
            text=response
        )
    ]


# ═══════════════════════════════════════════════════════════
# ONBOARDING TOOL HANDLERS
# ═══════════════════════════════════════════════════════════

async def handle_start_onboarding(arguments: dict) -> list[TextContent]:
    """Handle start_onboarding tool call."""
    import json

    user_id = arguments.get("user_id", "demo_user")
    result = start_onboarding(user_id)

    return [
        TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )
    ]


async def handle_store_answer(arguments: dict) -> list[TextContent]:
    """Handle store_answer tool call."""
    import json

    user_id = arguments.get("user_id", "demo_user")
    target_id = arguments.get("target_id")
    answer = arguments.get("answer", {})

    result = store_answer(user_id, target_id, answer)

    return [
        TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )
    ]


async def handle_get_next_question(arguments: dict) -> list[TextContent]:
    """Handle get_next_question tool call."""
    import json

    user_id = arguments.get("user_id", "demo_user")
    result = get_next_question(user_id)

    if result is None:
        result = {"status": "complete", "message": "Onboarding complete"}

    return [
        TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )
    ]


async def handle_complete_onboarding(arguments: dict) -> list[TextContent]:
    """Handle complete_onboarding tool call."""
    import json

    user_id = arguments.get("user_id", "demo_user")
    result = complete_onboarding(user_id)

    return [
        TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )
    ]


# ═══════════════════════════════════════════════════════════
# SERVER ENTRY POINT
# ═══════════════════════════════════════════════════════════

async def main():
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


if __name__ == "__main__":
    asyncio.run(main())
