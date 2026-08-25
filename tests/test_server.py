"""
Test MCP Server
================

Basic tests to verify the server starts and tools are registered correctly.
"""

import pytest
from src.server import app, handle_get_context


@pytest.mark.asyncio
async def test_server_has_tools():
    """Test that the server exposes the get_context tool."""
    # Import the decorated list_tools function directly
    from src.server import list_tools

    # Call the function to get tools
    tools = await list_tools()

    # Should have at least one tool
    assert len(tools) > 0

    # Should have get_context
    tool_names = [tool.name for tool in tools]
    assert "get_context" in tool_names


@pytest.mark.asyncio
async def test_get_context_returns_mock_data():
    """Test that get_context returns mock data (Segment 1 stub)."""
    arguments = {"query": "Write an email"}

    result = await handle_get_context(arguments)

    # Should return a list with one TextContent
    assert len(result) == 1
    assert result[0].type == "text"

    # Should contain mock profile data
    text = result[0].text
    assert "User Profile" in text
    assert "German" in text
    assert "MOCK data" in text


@pytest.mark.asyncio
async def test_get_context_with_empty_query():
    """Test that get_context handles empty query gracefully."""
    arguments = {"query": ""}

    result = await handle_get_context(arguments)

    # Should still return valid response
    assert len(result) == 1
    assert result[0].type == "text"
    assert len(result[0].text) > 0
