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

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent


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

    Currently returns MOCK data for testing.
    In later segments, this will:
    1. Load user profile from storage (Segment 2)
    2. Search for relevant outputs (Segment 3)
    3. Rank by relevance (most-relevant-first, Wu et al. 2024)
    4. Return structured context

    Args:
        arguments: {"query": str}

    Returns:
        List with one TextContent block containing the context
    """
    query = arguments.get("query", "")

    # MOCK DATA (Segment 1 stub)
    # This will be replaced with real data in Segment 2 & 3
    mock_response = f"""# Personalized Context for: "{query}"

## User Profile
- **Language:** German (de-DE)
- **Tone:** Professional but approachable (technical depth, no jargon overload)
- **Format Preference:** Concise with examples (bullet points preferred)
- **Boundaries:**
  - Avoid overly formal language ("Sie" is fine, but no corporate speak)
  - Technical user (VW Group, software architecture background)

## Relevant Past Outputs
(Ranked by relevance to current query)

1. **Email to team re: API design** (2026-07-15)
   - Clear structure: Context → Problem → Solution → Next steps
   - Used bullet points for action items
   - Technical but accessible

2. **Architecture document** (2026-07-10)
   - Started with "Why" before "How"
   - Included diagrams (LaTeX/Mermaid)
   - Decision log format

## Recent Context
- Currently working on: KIM project (MCP middleware)
- Recent topics: Claude Certified Architect prep, MCP protocol
- Ongoing: Segment-by-segment learning approach

---
*Note: This is MOCK data for Segment 1 testing.*
*Real profile/outputs will be loaded in Segment 2 & 3.*
"""

    return [
        TextContent(
            type="text",
            text=mock_response
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
