"""WhatsApp MCP Server implementation."""

import asyncio
import json
import logging
import sys
from enum import Enum
from typing import Any, Dict, List, Optional, TextIO, Union

from pydantic import BaseModel, ValidationError

from whatsapp_mcp.models import (
    CreateGroup, GroupParticipants, SendMessage, TextContent, ToolCall
)
from whatsapp_mcp.modules import auth, group, message

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)


class Tool(BaseModel):
    """Schema for tool definition."""
    name: str
    description: str
    inputSchema: Dict[str, Any]


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


class MCPServer:
    """Model Context Protocol (MCP) Server for WhatsApp."""
    
    def __init__(self, name: str = "whatsapp-mcp"):
        self.name = name
        self.auth_manager = auth.auth_manager
        self.current_session_id: Optional[str] = None
        self._tools: Dict[str, Tool] = {}
        self._register_tools()
    
    def _register_tools(self):
        """Register available tools."""
        tools = [
            Tool(
                name=WhatsAppTools.LIST_TOOLS,
                description="List available tools",
                inputSchema={}
            ),
            Tool(
                name=WhatsAppTools.CREATE_SESSION,
                description="Create a new WhatsApp session",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "session_id": {"type": "string", "description": "ID for the session"}
                    },
                    "required": ["session_id"]
                }
            ),
            Tool(
                name=WhatsAppTools.GET_QR_CODE,
                description="Get a QR code for authentication",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "session_id": {"type": "string", "description": "ID of the session"}
                    }
                }
            ),
            Tool(
                name=WhatsAppTools.AUTHENTICATE,
                description="Authenticate using QR code",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "session_id": {"type": "string", "description": "ID of the session"},
                        "qr_code": {"type": "string", "description": "QR code text"}
                    },
                    "required": ["qr_code"]
                }
            ),
            Tool(
                name=WhatsAppTools.LOGOUT,
                description="Logout from a session",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "session_id": {"type": "string", "description": "ID of the session"}
                    }
                }
            ),
            Tool(
                name=WhatsAppTools.SEND_MESSAGE,
                description="Send a message to a chat",
                inputSchema=SendMessage.model_json_schema()
            ),
            Tool(
                name=WhatsAppTools.GET_CHATS,
                description="Get a list of chats",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "session_id": {"type": "string", "description": "ID of the session"},
                        "limit": {"type": "integer", "description": "Maximum number of chats to return"},
                        "offset": {"type": "integer", "description": "Offset for pagination"}
                    }
                }
            ),
            Tool(
                name=WhatsAppTools.CREATE_GROUP,
                description="Create a new WhatsApp group",
                inputSchema=CreateGroup.model_json_schema()
            ),
            Tool(
                name=WhatsAppTools.GET_GROUP_PARTICIPANTS,
                description="Get the participants of a WhatsApp group",
                inputSchema=GroupParticipants.model_json_schema()
            )
        ]
        
        for tool in tools:
            self._tools[tool.name] = tool
    
    async def list_tools(self) -> List[Tool]:
        """List available tools."""
        return list(self._tools.values())
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> List[TextContent]:
        """Call a tool with the given arguments."""
        try:
            match name:
                case WhatsAppTools.LIST_TOOLS:
                    tools = await self.list_tools()
                    return [TextContent(type="text", text=json.dumps([tool.model_dump() for tool in tools]))]
                
                case WhatsAppTools.CREATE_SESSION:
                    session_id = arguments.get("session_id")
                    if not session_id:
                        return [TextContent(type="text", text="Error: session_id is required")]
                    
                    success, message_text = await self.auth_manager.create_session(session_id)
                    if success:
                        self.current_session_id = session_id
                        return [TextContent(type="text", text=f"Success: {message_text}")]
                    else:
                        return [TextContent(type="text", text=f"Error: {message_text}")]
                
                case WhatsAppTools.GET_QR_CODE:
                    session_id = arguments.get("session_id") or self.current_session_id
                    if not session_id:
                        return [TextContent(type="text", text="Error: No active session")]
                    
                    qr_code = await self.auth_manager.get_qr_code(session_id)
                    if qr_code:
                        return [TextContent(type="text", text=json.dumps(qr_code.model_dump()))]
                    else:
                        return [TextContent(type="text", text="Error: Failed to generate QR code")]
                
                case WhatsAppTools.AUTHENTICATE:
                    session_id = arguments.get("session_id") or self.current_session_id
                    qr_code = arguments.get("qr_code")
                    
                    if not session_id:
                        return [TextContent(type="text", text="Error: No active session")]
                    
                    if not qr_code:
                        return [TextContent(type="text", text="Error: qr_code is required")]
                    
                    success = await self.auth_manager.authenticate(session_id, qr_code)
                    if success:
                        return [TextContent(type="text", text="Success: Authentication successful")]
                    else:
                        return [TextContent(type="text", text="Error: Authentication failed")]
                
                case WhatsAppTools.LOGOUT:
                    session_id = arguments.get("session_id") or self.current_session_id
                    
                    if not session_id:
                        return [TextContent(type="text", text="Error: No active session")]
                    
                    success = await self.auth_manager.logout(session_id)
                    if success:
                        if session_id == self.current_session_id:
                            self.current_session_id = None
                        return [TextContent(type="text", text="Success: Logout successful")]
                    else:
                        return [TextContent(type="text", text="Error: Logout failed")]
                
                case WhatsAppTools.SEND_MESSAGE:
                    session_id = arguments.get("session_id") or self.current_session_id
                    
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
                    session_id = arguments.get("session_id") or self.current_session_id
                    
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
                    session_id = arguments.get("session_id") or self.current_session_id
                    
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
                    session_id = arguments.get("session_id") or self.current_session_id
                    
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
    
    async def process_message(self, data: dict):
        """Process an incoming message."""
        try:
            if "name" in data and "arguments" in data:
                # This is a tool call
                name = data["name"]
                arguments = data["arguments"]
                return await self.call_tool(name, arguments)
            else:
                # Invalid message format
                return [TextContent(type="text", text="Error: Invalid message format. Expected tool call.")]
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return [TextContent(type="text", text=f"Error: {str(e)}")]
    
    async def run(self, input_stream: TextIO, output_stream: TextIO):
        """Run the server with the given input and output streams."""
        while True:
            try:
                # Read a line from input
                line = await asyncio.to_thread(input_stream.readline)
                
                if not line:
                    break
                
                try:
                    # Parse the JSON data
                    data = json.loads(line)
                    
                    # Process the message
                    results = await self.process_message(data)
                    
                    # Write the results to output
                    for result in results:
                        output_stream.write(json.dumps(result.model_dump()) + "\n")
                        output_stream.flush()
                
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to decode JSON: {e}")
                    output_stream.write(json.dumps(TextContent(type="text", text=f"Error: Invalid JSON: {e}").model_dump()) + "\n")
                    output_stream.flush()
                
                except Exception as e:
                    logger.error(f"Error processing request: {e}")
                    output_stream.write(json.dumps(TextContent(type="text", text=f"Error: {str(e)}").model_dump()) + "\n")
                    output_stream.flush()
            
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                try:
                    output_stream.write(json.dumps(TextContent(type="text", text=f"Error: {str(e)}").model_dump()) + "\n")
                    output_stream.flush()
                except:
                    pass


async def main():
    """Run the MCP server."""
    server = MCPServer()
    try:
        await server.run(sys.stdin, sys.stdout)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())