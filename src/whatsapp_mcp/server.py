"""WhatsApp MCP Server implementation."""

import json
import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator, Dict, Any, Optional

from mcp.server.fastmcp import FastMCP, Context

from whatsapp_mcp.modules import auth, group, message

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# Global state for the current session
current_session_id: Optional[str] = None


@asynccontextmanager
async def server_lifespan(server: FastMCP) -> AsyncIterator[Dict[str, Any]]:
    """Manage server startup and shutdown lifecycle."""
    try:
        # Log server startup
        logger.info("WhatsApp MCP Server starting up")
        yield {}
    finally:
        # Cleanup resources when shutting down
        logger.info("WhatsApp MCP Server shutting down")


# Create the FastMCP server with lifespan support
mcp = FastMCP(
    "WhatsAppMCP",
    description="WhatsApp integration through the Model Context Protocol",
    lifespan=server_lifespan,
)


@mcp.tool()
async def open_session(ctx: Context) -> str:
    """Open a new WhatsApp session."""
    try:
        # Open a new session
        success, message_text = await auth.auth_manager.open_session()
        if success:
            return f"Success: {message_text}"
        else:
            return f"Error: {message_text}"
    except Exception as e:
        logger.error(f"Error opening session: {e}")
        return f"Error: {str(e)}"


@mcp.tool()
async def send_message(
    ctx: Context, phone_number: str, content: str, reply_to: Optional[str] = None
) -> str:
    """
    Send a message to a chat.

    Parameters:
    - phone_number: The phone number of the recipient
    - content: The content of the message to send
    - reply_to: ID of the message to reply to (optional)
    """
    try:
        if not auth.auth_manager.is_authenticated():
            return "Error: No active session"

        result = await message.send_message(
            phone_number=phone_number, content=content, reply_to=reply_to
        )
        return json.dumps(result)
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        return f"Error: {str(e)}"


@mcp.tool()
async def get_chats(ctx: Context, limit: int = 50, offset: int = 0) -> str:
    """
    Get a list of chats.

    Parameters:
    - limit: Maximum number of chats to return (default: 50)
    - offset: Offset for pagination (default: 0)
    """
    try:
        if not auth.auth_manager.is_authenticated():
            return "Error: No active session"

        chats = await message.get_chats(limit=limit, offset=offset)
        return json.dumps({"chats": chats})
    except Exception as e:
        logger.error(f"Error getting chats: {e}")
        return f"Error: {str(e)}"


@mcp.tool()
async def create_group(ctx: Context, group_name: str, participants: list[str]) -> str:
    """
    Create a new WhatsApp group.

    Parameters:
    - group_name: Name of the group to create
    - participants: List of participant phone numbers
    """
    try:
        if not auth.auth_manager.is_authenticated():
            return "Error: No active session"

        group_result = await group.create_group(
            group_name=group_name,
            participants=participants,
        )
        return json.dumps(group_result.model_dump())
    except Exception as e:
        logger.error(f"Error creating group: {e}")
        return f"Error: {str(e)}"


@mcp.tool()
async def get_group_participants(ctx: Context, group_id: str) -> str:
    """
    Get the participants of a WhatsApp group.

    Parameters:
    - group_id: The WhatsApp ID of the group
    """
    try:
        if not auth.auth_manager.is_authenticated():
            return "Error: No active session"

        participants = await group.get_group_participants(group_id=group_id)
        return json.dumps({"participants": [p.model_dump() for p in participants]})
    except Exception as e:
        logger.error(f"Error getting group participants: {e}")
        return f"Error: {str(e)}"

