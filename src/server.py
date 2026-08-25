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
        )
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

    # Build full context response
    response = f"""# Personalized Context for: "{query}"

{profile_text}

## Relevant Past Outputs
*(Segment 3 - Retrieval engine not yet implemented)*

Will include:
- Past outputs ranked by relevance to current query
- Most-relevant-first ordering (Wu et al. 2024)
- BM25 + vector similarity hybrid ranking

---
*Profile loaded from: ~/.kim/data/profiles/{profile.id}.json*
*Next: Segment 3 will add retrieval engine*
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
