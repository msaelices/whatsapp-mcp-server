"""Tests for the server module."""

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from whatsapp_mcp.models import MCP_Message, MCP_MessageType, TextContent
from whatsapp_mcp.server import MCPServer


@pytest.fixture
def server():
    """Fixture for MCPServer instance."""
    return MCPServer()


@patch("whatsapp_mcp.modules.auth.auth_manager")
def test_list_tools(mock_auth_manager, server):
    """Test listing tools."""
    # Create async function to run the test
    async def run_test():
        server.send_tool_result = AsyncMock()
        await server.handle_tool_call("list_tools", {})
        server.send_tool_result.assert_called_once()
        
        # Check that the tools list contains expected tools
        tools = server.send_tool_result.call_args[0][0]
        tool_names = [tool["name"] for tool in tools]
        
        assert "list_tools" in tool_names
        assert "create_session" in tool_names
        assert "send_message" in tool_names
        assert "get_group_participants" in tool_names
    
    # Run the async test
    asyncio.run(run_test())


@patch("whatsapp_mcp.modules.auth.auth_manager")
def test_create_session(mock_auth_manager, server):
    """Test creating a session."""
    # Setup mock
    mock_auth_manager.create_session = AsyncMock(return_value=(True, "Session created successfully"))
    
    # Create async function to run the test
    async def run_test():
        server.send_tool_result = AsyncMock()
        server.send_error = AsyncMock()
        
        # Test with valid arguments
        await server.handle_tool_call("create_session", {"session_id": "test_session"})
        server.send_tool_result.assert_called_once()
        assert server.current_session_id == "test_session"
        
        # Reset mocks
        server.send_tool_result.reset_mock()
        server.send_error.reset_mock()
        
        # Test with missing session_id
        await server.handle_tool_call("create_session", {})
        server.send_error.assert_called_once()
    
    # Run the async test
    asyncio.run(run_test())


@patch("whatsapp_mcp.modules.auth.auth_manager")
def test_process_message(mock_auth_manager, server):
    """Test processing messages."""
    # Create async function to run the test
    async def run_test():
        server.send_text = AsyncMock()
        server.send_error = AsyncMock()
        server.handle_tool_call = AsyncMock()
        
        # Test with text message
        text_message = MCP_Message(
            type=MCP_MessageType.TEXT,
            content=TextContent(text="Hello, world!")
        )
        await server.process_message(text_message)
        server.send_text.assert_called_once()
        
        # Reset mocks
        server.send_text.reset_mock()
        server.send_error.reset_mock()
        
        # Test with tool call
        tool_call_message = MCP_Message(
            type=MCP_MessageType.TOOL_CALL,
            content={"name": "list_tools", "arguments": {}}
        )
        await server.process_message(tool_call_message)
        server.handle_tool_call.assert_called_once_with("list_tools", {})
    
    # Run the async test
    asyncio.run(run_test())


@patch("whatsapp_mcp.modules.auth.auth_manager")
def test_send_message(mock_auth_manager, server):
    """Test sending a message."""
    # Create async function to run the test
    async def run_test():
        # Mock print function to capture output
        with patch("builtins.print") as mock_print:
            # Send a text message
            await server.send_text("Hello, world!")
            
            # Check that print was called with a JSON string
            mock_print.assert_called_once()
            output = mock_print.call_args[0][0]
            
            # Parse the JSON output and check the message
            message = json.loads(output)
            assert message["type"] == "text"
            assert message["content"]["type"] == "text"
            assert message["content"]["text"] == "Hello, world!"
    
    # Run the async test
    asyncio.run(run_test())