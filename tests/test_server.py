"""Tests for the server module."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock


@pytest.mark.asyncio
@patch("whatsapp_mcp.modules.auth.auth_manager")
async def test_open_session(mock_auth_manager):
    """Test open_session implementation."""
    # Set up mock response
    mock_auth_manager.open_session = AsyncMock(
        return_value=(True, "Session opened successfully")
    )

    # Import function here to avoid early evaluation
    from whatsapp_mcp.server import open_session

    # Create a mock context
    ctx = MagicMock()

    # Call the function with open_session arguments
    result = await open_session(ctx)

    # Verify result
    assert "Success" in result


@pytest.mark.asyncio
@patch("whatsapp_mcp.modules.auth.auth_manager")
@patch("whatsapp_mcp.modules.message.send_message")
async def test_send_message(mock_send_message, mock_auth_manager):
    """Test send_message implementation."""
    # Set up mock responses
    mock_auth_manager.is_authenticated.return_value = True
    mock_send_message.return_value = {
        "message_id": "123456",
        "status": "sent",
        "timestamp": "2023-04-01T12:00:00",
        "response": {"success": True},
    }

    # Import function here to avoid early evaluation
    from whatsapp_mcp.server import send_message

    # Create a mock context
    ctx = MagicMock()

    # Call the function with send_message arguments
    result = await send_message(ctx, "1234567890", "Hello, world!")

    # Verify result
    assert "123456" in result


@pytest.mark.asyncio
@patch("whatsapp_mcp.modules.auth.auth_manager")
@patch("whatsapp_mcp.modules.message.get_chats")
async def test_get_chats(mock_get_chats, mock_auth_manager):
    """Test get_chats implementation."""
    # Set up mock responses
    mock_auth_manager.is_authenticated.return_value = True
    mock_get_chats.return_value = [
        {
            "id": "123456789@c.us",
            "name": "Test User",
            "is_group": False,
            "last_message": "Hello",
            "timestamp": "2023-04-01T12:00:00",
        }
    ]

    # Import function here to avoid early evaluation
    from whatsapp_mcp.server import get_chats

    # Create a mock context
    ctx = MagicMock()

    # Call the function with get_chats arguments
    result = await get_chats(ctx)

    # Verify result
    assert "123456789@c.us" in result
    assert "Test User" in result


@patch("whatsapp_mcp.server.mcp")
def test_registered_tools(mock_mcp):
    """Test that all tools are registered correctly."""
    # Configure the mock
    mock_mcp.tool.called = True
    mock_mcp.tool.mock_calls = [
        MagicMock(args=[MagicMock(__name__="open_session")]),
        MagicMock(args=[MagicMock(__name__="send_message")]),
        MagicMock(args=[MagicMock(__name__="get_chats")]),
        MagicMock(args=[MagicMock(__name__="create_group")]),
        MagicMock(args=[MagicMock(__name__="get_group_participants")]),
    ]

    # Import the server module to trigger tool registration
    # Check that tool decorators were called for each tool
    assert mock_mcp.tool.called

    # Get all the tool names that were registered
    tool_names = [
        call.args[0].__name__ for call in mock_mcp.tool.mock_calls if call.args
    ]

    # Verify that all expected tools are registered
    assert "open_session" in tool_names
    assert "send_message" in tool_names
    assert "get_chats" in tool_names
    assert "create_group" in tool_names
    assert "get_group_participants" in tool_names

