"""
KIM MCP Server
==============

Entry point for the KIM MCP middleware server.

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
from mcp.types import Tool, TextContent

from src.profile import get_or_create_profile, format_profile_for_llm
from src.retrieval.hybrid import retrieve_relevant_outputs, format_outputs_for_llm
from src.tools.log_output import get_log_output_tool, handle_log_output


# ═══════════════════════════════════════════════════════════
# SERVER INSTANCE
# ═══════════════════════════════════════════════════════════

app = Server("kim-server")


# ═══════════════════════════════════════════════════════════
# TOOL: get_context
# ═══════════════════════════════════════════════════════════

@app.list_tools()
async def list_tools() -> list[Tool]:
    """
    Register all available tools.

    This is called by MCP clients to discover what tools are available.
    """
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
        get_log_output_tool()
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
    if name == "get_context":
        return await handle_get_context(arguments)

    if name == "log_output":
        # TODO: Get user_id from MCP session context
        demo_user_id = UUID("00000000-0000-0000-0000-000000000001")
        return await handle_log_output(arguments, demo_user_id)

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

    # TODO: Get user_id from MCP session context
    # For now, use a fixed demo user ID
    # In production, this would come from authentication
    demo_user_id = UUID("00000000-0000-0000-0000-000000000001")

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

    # Build full context response
    response = f"""# Personalized Context for: "{query}"

{profile_text}

## Relevant Past Outputs
{outputs_text}

---
*Profile loaded from: ~/.kim/profiles/{profile.id}.json*
*Retrieval: Hybrid BM25 + vector similarity (Wu et al. 2024)*
"""

    return [
        TextContent(
            type="text",
            text=response
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
