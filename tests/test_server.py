"""Tests for the server module."""

import pytest
from unittest.mock import AsyncMock, patch


from whatsapp_mcp.server import WhatsAppTools


@pytest.mark.asyncio
async def test_whatsapp_tools_enum():
    """Test the WhatsAppTools enum."""
    # Check that all expected tools are defined
    assert WhatsAppTools.CREATE_SESSION == "create_session"
    assert WhatsAppTools.SEND_MESSAGE == "send_message"
    assert WhatsAppTools.GET_CHATS == "get_chats"
    assert WhatsAppTools.CREATE_GROUP == "create_group"
    assert WhatsAppTools.GET_GROUP_PARTICIPANTS == "get_group_participants"


@pytest.mark.asyncio
@patch("whatsapp_mcp.modules.auth.auth_manager")
async def test_create_session(mock_auth_manager):
    """Test create_session implementation."""
    # Set up mock response
    mock_auth_manager.create_session = AsyncMock(
        return_value=(True, "Session created successfully")
    )

    # Import function here to avoid early evaluation
    from whatsapp_mcp.server import call_tool

    # Call the function with create_session arguments
    result = await call_tool("create_session")

    # Verify result
    assert len(result) == 1
    assert result[0].type == "text"
    assert "Success" in result[0].text


@pytest.mark.asyncio
async def test_list_tools():
    """Test list_tools implementation."""
    # Import function here to avoid early evaluation
    from whatsapp_mcp.server import list_tools

    # Call the function
    tools = await list_tools()

    # Verify result
    assert len(tools) > 0
    tool_names = [tool.name for tool in tools]

    # Check that all expected tools are in the list
    assert "create_session" in tool_names
    assert "send_message" in tool_names
    assert "get_chats" in tool_names
    assert "create_group" in tool_names
    assert "get_group_participants" in tool_names

