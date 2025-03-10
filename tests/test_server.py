"""Tests for the server module."""

import asyncio
import io
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from whatsapp_mcp.models import TextContent
from whatsapp_mcp.server import MCPServer, Tool


@pytest.fixture
def server():
    """Fixture for MCPServer instance."""
    return MCPServer()


def test_register_tools(server):
    """Test tool registration."""
    # Check that tools were registered
    assert len(server._tools) > 0
    
    # Check that required tools are present
    assert "list_tools" in server._tools
    assert "create_session" in server._tools
    assert "send_message" in server._tools
    assert "get_group_participants" in server._tools


@patch("whatsapp_mcp.modules.auth.auth_manager")
def test_list_tools(mock_auth_manager, server):
    """Test listing tools."""
    # Create async function to run the test
    async def run_test():
        tools = await server.list_tools()
        
        # Check that the tools list contains expected tools
        tool_names = [tool.name for tool in tools]
        
        assert "list_tools" in tool_names
        assert "create_session" in tool_names
        assert "send_message" in tool_names
        assert "get_group_participants" in tool_names
    
    # Run the async test
    asyncio.run(run_test())


@patch("whatsapp_mcp.modules.auth.auth_manager")
def test_call_tool_list_tools(mock_auth_manager, server):
    """Test calling the list_tools tool."""
    # Create async function to run the test
    async def run_test():
        result = await server.call_tool("list_tools", {})
        
        # Check the result
        assert len(result) == 1
        assert result[0].type == "text"
        
        # Parse the JSON string in the text field
        tools = json.loads(result[0].text)
        tool_names = [tool["name"] for tool in tools]
        
        assert "list_tools" in tool_names
        assert "create_session" in tool_names
        assert "send_message" in tool_names
        assert "get_group_participants" in tool_names
    
    # Run the async test
    asyncio.run(run_test())


@patch("whatsapp_mcp.modules.auth.auth_manager")
def test_call_tool_create_session(mock_auth_manager, server):
    """Test calling the create_session tool."""
    # Setup mock
    mock_auth_manager.create_session = AsyncMock(return_value=(True, "Session created successfully"))
    
    # Create async function to run the test
    async def run_test():
        # Test with valid arguments
        result = await server.call_tool("create_session", {"session_id": "test_session"})
        
        # Check the result
        assert len(result) == 1
        assert result[0].type == "text"
        assert "Success" in result[0].text
        assert server.current_session_id == "test_session"
        
        # Test with missing session_id
        result = await server.call_tool("create_session", {})
        
        # Check the result
        assert len(result) == 1
        assert result[0].type == "text"
        assert "Error" in result[0].text
    
    # Run the async test
    asyncio.run(run_test())


@patch("whatsapp_mcp.modules.auth.auth_manager")
def test_process_message(mock_auth_manager):
    """Test processing messages."""
    # Create a fresh server for this test
    server = MCPServer()
    
    # Setup mock
    mock_auth_manager.create_session = AsyncMock(return_value=(True, "Session created successfully"))
    
    # Create async function to run the test
    async def run_test():
        # Test with valid tool call
        result = await server.process_message({
            "name": "create_session",
            "arguments": {"session_id": "test_session"}
        })
        
        # Check the result
        assert len(result) == 1
        assert result[0].type == "text"
        assert "Success" in result[0].text
        assert server.current_session_id == "test_session"
        
        # Test with invalid message format
        result = await server.process_message({"invalid": "format"})
        
        # Check the result
        assert len(result) == 1
        assert result[0].type == "text"
        assert "Error" in result[0].text
    
    # Run the async test
    asyncio.run(run_test())


@patch("whatsapp_mcp.modules.auth.auth_manager")
def test_run(mock_auth_manager):
    """Test the run method."""
    # Create a fresh server for this test
    server = MCPServer()
    
    # Setup mock
    mock_auth_manager.create_session = AsyncMock(return_value=(True, "Session created successfully"))
    
    # Create mock input and output streams
    input_stream = io.StringIO('{"name": "create_session", "arguments": {"session_id": "test_session"}}\n')
    output_stream = io.StringIO()
    
    # Create async function to run the test
    async def run_test():
        # Run with a single input
        task = asyncio.create_task(server.run(input_stream, output_stream))
        
        # Wait a short time to allow processing
        await asyncio.sleep(0.1)
        
        # Cancel the task (otherwise it would wait forever for more input)
        task.cancel()
        
        try:
            await task
        except asyncio.CancelledError:
            pass
        
        # Check the output
        output = output_stream.getvalue()
        assert output
        
        # Parse the JSON output
        result = json.loads(output.strip())
        assert result["type"] == "text"
        assert "Success" in result["text"]
    
    # Run the async test
    asyncio.run(run_test())