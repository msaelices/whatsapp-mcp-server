"""WhatsApp MCP Server implementation."""

import asyncio
import json
import logging
import sys
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from pydantic import BaseModel, Field, ValidationError

from whatsapp_mcp.models import (
    CreateGroup, GroupParticipants, SendMessage
)
from whatsapp_mcp.modules import auth, group, message

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)


class WhatsAppTools(str, Enum):
    """WhatsApp MCP tools."""
    LIST_TOOLS = "list_tools"
    CREATE_SESSION = "create_session"
    GET_QR_CODE = "get_qr_code"
    AUTHENTICATE = "authenticate"
    LOGOUT = "logout"
    SEND_MESSAGE = "send_message"
    GET_CHATS = "get_chats"
    CREATE_GROUP = "create_group"
    GET_GROUP_PARTICIPANTS = "get_group_participants"


class CreateSessionModel(BaseModel):
    """Input schema for create_session tool."""
    session_id: str = Field(..., description="ID for the session")


class GetQRCodeModel(BaseModel):
    """Input schema for get_qr_code tool."""
    session_id: Optional[str] = Field(None, description="ID of the session")


class AuthenticateModel(BaseModel):
    """Input schema for authenticate tool."""
    session_id: Optional[str] = Field(None, description="ID of the session")
    qr_code: str = Field(..., description="QR code text")


class LogoutModel(BaseModel):
    """Input schema for logout tool."""
    session_id: Optional[str] = Field(None, description="ID of the session")


class GetChatsModel(BaseModel):
    """Input schema for get_chats tool."""
    session_id: Optional[str] = Field(None, description="ID of the session")
    limit: int = Field(50, description="Maximum number of chats to return")
    offset: int = Field(0, description="Offset for pagination")


# Global state for the current session
current_session_id: Optional[str] = None


async def serve():
    """Run the WhatsApp MCP server."""
    global current_session_id
    
    logger.info("Starting WhatsApp MCP Server")
    server = Server("whatsapp-mcp")
    
    @server.list_tools()
    async def list_tools() -> list[Tool]:
        """List available tools."""
        return [
            Tool(
                name=WhatsAppTools.CREATE_SESSION,
                description="Create a new WhatsApp session",
                inputSchema=CreateSessionModel.model_json_schema(),
            ),
            Tool(
                name=WhatsAppTools.GET_QR_CODE,
                description="Get a QR code for authentication",
                inputSchema=GetQRCodeModel.model_json_schema(),
            ),
            Tool(
                name=WhatsAppTools.AUTHENTICATE,
                description="Authenticate using QR code",
                inputSchema=AuthenticateModel.model_json_schema(),
            ),
            Tool(
                name=WhatsAppTools.LOGOUT,
                description="Logout from a session",
                inputSchema=LogoutModel.model_json_schema(),
            ),
            Tool(
                name=WhatsAppTools.SEND_MESSAGE,
                description="Send a message to a chat",
                inputSchema=SendMessage.model_json_schema(),
            ),
            Tool(
                name=WhatsAppTools.GET_CHATS,
                description="Get a list of chats",
                inputSchema=GetChatsModel.model_json_schema(),
            ),
            Tool(
                name=WhatsAppTools.CREATE_GROUP,
                description="Create a new WhatsApp group",
                inputSchema=CreateGroup.model_json_schema(),
            ),
            Tool(
                name=WhatsAppTools.GET_GROUP_PARTICIPANTS,
                description="Get the participants of a WhatsApp group",
                inputSchema=GroupParticipants.model_json_schema(),
            ),
        ]
    
    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[TextContent]:
        """Call a tool with the given arguments."""
        global current_session_id
        
        try:
            match name:
                case WhatsAppTools.CREATE_SESSION:
                    # Create a new session
                    session_id = arguments.get("session_id")
                    if not session_id:
                        return [TextContent(type="text", text="Error: session_id is required")]
                    
                    success, message_text = await auth.auth_manager.create_session(session_id)
                    if success:
                        current_session_id = session_id
                        return [TextContent(type="text", text=f"Success: {message_text}")]
                    else:
                        return [TextContent(type="text", text=f"Error: {message_text}")]
                
                case WhatsAppTools.GET_QR_CODE:
                    # Get a QR code for authentication
                    session_id = arguments.get("session_id") or current_session_id
                    if not session_id:
                        return [TextContent(type="text", text="Error: No active session")]
                    
                    qr_code = await auth.auth_manager.get_qr_code(session_id)
                    if qr_code:
                        return [TextContent(type="text", text=json.dumps(qr_code.model_dump()))]
                    else:
                        return [TextContent(type="text", text="Error: Failed to generate QR code")]
                
                case WhatsAppTools.AUTHENTICATE:
                    # Authenticate using QR code
                    session_id = arguments.get("session_id") or current_session_id
                    qr_code = arguments.get("qr_code")
                    
                    if not session_id:
                        return [TextContent(type="text", text="Error: No active session")]
                    
                    if not qr_code:
                        return [TextContent(type="text", text="Error: qr_code is required")]
                    
                    success = await auth.auth_manager.authenticate(session_id, qr_code)
                    if success:
                        return [TextContent(type="text", text="Success: Authentication successful")]
                    else:
                        return [TextContent(type="text", text="Error: Authentication failed")]
                
                case WhatsAppTools.LOGOUT:
                    # Logout from a session
                    session_id = arguments.get("session_id") or current_session_id
                    
                    if not session_id:
                        return [TextContent(type="text", text="Error: No active session")]
                    
                    success = await auth.auth_manager.logout(session_id)
                    if success:
                        if session_id == current_session_id:
                            current_session_id = None
                        return [TextContent(type="text", text="Success: Logout successful")]
                    else:
                        return [TextContent(type="text", text="Error: Logout failed")]
                
                case WhatsAppTools.SEND_MESSAGE:
                    # Send a message
                    session_id = arguments.get("session_id") or current_session_id
                    
                    if not session_id:
                        return [TextContent(type="text", text="Error: No active session")]
                    
                    try:
                        send_message_args = SendMessage.model_validate(arguments)
                        result = await message.send_message(
                            session_id=session_id,
                            chat_id=send_message_args.chat_id,
                            content=send_message_args.content,
                            reply_to=send_message_args.reply_to
                        )
                        return [TextContent(type="text", text=json.dumps(result))]
                    except ValidationError as e:
                        return [TextContent(type="text", text=f"Error: Invalid arguments: {e}")]
                    except Exception as e:
                        return [TextContent(type="text", text=f"Error: Failed to send message: {e}")]
                
                case WhatsAppTools.GET_CHATS:
                    # Get chats
                    session_id = arguments.get("session_id") or current_session_id
                    
                    if not session_id:
                        return [TextContent(type="text", text="Error: No active session")]
                    
                    limit = arguments.get("limit", 50)
                    offset = arguments.get("offset", 0)
                    
                    try:
                        chats = await message.get_chats(
                            session_id=session_id,
                            limit=limit,
                            offset=offset
                        )
                        return [TextContent(type="text", text=json.dumps({"chats": chats}))]
                    except Exception as e:
                        return [TextContent(type="text", text=f"Error: Failed to get chats: {e}")]
                
                case WhatsAppTools.CREATE_GROUP:
                    # Create a group
                    session_id = arguments.get("session_id") or current_session_id
                    
                    if not session_id:
                        return [TextContent(type="text", text="Error: No active session")]
                    
                    try:
                        create_group_args = CreateGroup.model_validate(arguments)
                        result = await group.create_group(
                            session_id=session_id,
                            group_name=create_group_args.group_name,
                            participants=create_group_args.participants
                        )
                        return [TextContent(type="text", text=json.dumps(result.model_dump()))]
                    except ValidationError as e:
                        return [TextContent(type="text", text=f"Error: Invalid arguments: {e}")]
                    except Exception as e:
                        return [TextContent(type="text", text=f"Error: Failed to create group: {e}")]
                
                case WhatsAppTools.GET_GROUP_PARTICIPANTS:
                    # Get group participants
                    session_id = arguments.get("session_id") or current_session_id
                    
                    if not session_id:
                        return [TextContent(type="text", text="Error: No active session")]
                    
                    try:
                        group_participants_args = GroupParticipants.model_validate(arguments)
                        participants = await group.get_group_participants(
                            session_id=session_id,
                            group_id=group_participants_args.group_id
                        )
                        return [TextContent(type="text", text=json.dumps({"participants": [p.model_dump() for p in participants]}))]
                    except ValidationError as e:
                        return [TextContent(type="text", text=f"Error: Invalid arguments: {e}")]
                    except Exception as e:
                        return [TextContent(type="text", text=f"Error: Failed to get group participants: {e}")]
                
                case _:
                    return [TextContent(type="text", text=f"Error: Unknown tool: {name}")]
        
        except Exception as e:
            logger.error(f"Error handling tool call: {e}")
            return [TextContent(type="text", text=f"Error: {str(e)}")]
    
    # Run the server
    options = server.create_initialization_options()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, options, raise_exceptions=True)