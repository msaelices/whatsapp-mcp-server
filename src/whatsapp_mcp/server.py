"""WhatsApp MCP Server implementation."""

import asyncio
import json
import logging
import sys
from typing import Any, Dict, List, Optional, Union

from pydantic import ValidationError

from whatsapp_mcp.models import (
    CreateGroup, GroupParticipants, MCP_Message, MCP_MessageType,
    SendMessage, TextContent, Tool, ToolCall
)
from whatsapp_mcp.modules import auth, group, message

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)


class MCPServer:
    """Model Context Protocol (MCP) Server for WhatsApp."""
    
    def __init__(self):
        self.auth_manager = auth.auth_manager
        self.current_session_id: Optional[str] = None
    
    async def handle_input(self):
        """Read from stdin and handle the input."""
        while True:
            try:
                # Read a line from stdin
                line = await asyncio.to_thread(sys.stdin.readline)
                
                if not line:
                    break
                
                # Parse the JSON input
                try:
                    data = json.loads(line)
                    message = MCP_Message.model_validate(data)
                    await self.process_message(message)
                except ValidationError as e:
                    logger.error(f"Failed to parse message: {e}")
                    await self.send_error("Failed to parse message")
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to decode JSON: {e}")
                    await self.send_error("Failed to decode JSON")
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    await self.send_error(f"Error: {str(e)}")
            
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                await self.send_error(f"Unexpected error: {str(e)}")
    
    async def process_message(self, message: MCP_Message):
        """Process an MCP message."""
        if message.type == MCP_MessageType.TEXT:
            # Handle text message
            if isinstance(message.content, TextContent):
                text = message.content.text
                await self.send_text(f"Received text: {text}")
            else:
                await self.send_error("Invalid text content")
        
        elif message.type == MCP_MessageType.TOOL_CALL:
            # Handle tool call
            if isinstance(message.content, ToolCall) or isinstance(message.content, dict):
                if isinstance(message.content, dict):
                    content = ToolCall.model_validate(message.content)
                else:
                    content = message.content
                    
                await self.handle_tool_call(content.name, content.arguments)
            else:
                await self.send_error("Invalid tool call content")
    
    async def handle_tool_call(self, name: str, arguments: Dict[str, Any]):
        """Handle a tool call."""
        try:
            if name == "list_tools":
                # Return list of available tools
                tools = await self.list_tools()
                await self.send_tool_result(tools)
            
            elif name == "create_session":
                # Create a new session
                session_id = arguments.get("session_id")
                if not session_id:
                    await self.send_error("session_id is required")
                    return
                
                success, message = await self.auth_manager.create_session(session_id)
                if success:
                    self.current_session_id = session_id
                    await self.send_tool_result({"success": True, "message": message})
                else:
                    await self.send_error(message)
            
            elif name == "get_qr_code":
                # Get a QR code for authentication
                session_id = arguments.get("session_id") or self.current_session_id
                if not session_id:
                    await self.send_error("No active session")
                    return
                
                qr_code = await self.auth_manager.get_qr_code(session_id)
                if qr_code:
                    await self.send_tool_result(qr_code.model_dump())
                else:
                    await self.send_error("Failed to generate QR code")
            
            elif name == "authenticate":
                # Authenticate using QR code
                session_id = arguments.get("session_id") or self.current_session_id
                qr_code = arguments.get("qr_code")
                
                if not session_id:
                    await self.send_error("No active session")
                    return
                
                if not qr_code:
                    await self.send_error("qr_code is required")
                    return
                
                success = await self.auth_manager.authenticate(session_id, qr_code)
                if success:
                    await self.send_tool_result({"success": True, "message": "Authentication successful"})
                else:
                    await self.send_error("Authentication failed")
            
            elif name == "logout":
                # Logout from a session
                session_id = arguments.get("session_id") or self.current_session_id
                
                if not session_id:
                    await self.send_error("No active session")
                    return
                
                success = await self.auth_manager.logout(session_id)
                if success:
                    if session_id == self.current_session_id:
                        self.current_session_id = None
                    await self.send_tool_result({"success": True, "message": "Logout successful"})
                else:
                    await self.send_error("Logout failed")
            
            elif name == "send_message":
                # Send a message
                session_id = arguments.get("session_id") or self.current_session_id
                
                if not session_id:
                    await self.send_error("No active session")
                    return
                
                try:
                    send_message_args = SendMessage.model_validate(arguments)
                    result = await message.send_message(
                        session_id=session_id,
                        chat_id=send_message_args.chat_id,
                        content=send_message_args.content,
                        reply_to=send_message_args.reply_to
                    )
                    await self.send_tool_result(result)
                except ValidationError as e:
                    await self.send_error(f"Invalid arguments: {e}")
                except Exception as e:
                    await self.send_error(f"Failed to send message: {e}")
            
            elif name == "get_chats":
                # Get chats
                session_id = arguments.get("session_id") or self.current_session_id
                
                if not session_id:
                    await self.send_error("No active session")
                    return
                
                limit = arguments.get("limit", 50)
                offset = arguments.get("offset", 0)
                
                try:
                    chats = await message.get_chats(
                        session_id=session_id,
                        limit=limit,
                        offset=offset
                    )
                    await self.send_tool_result({"chats": chats})
                except Exception as e:
                    await self.send_error(f"Failed to get chats: {e}")
            
            elif name == "create_group":
                # Create a group
                session_id = arguments.get("session_id") or self.current_session_id
                
                if not session_id:
                    await self.send_error("No active session")
                    return
                
                try:
                    create_group_args = CreateGroup.model_validate(arguments)
                    result = await group.create_group(
                        session_id=session_id,
                        group_name=create_group_args.group_name,
                        participants=create_group_args.participants
                    )
                    await self.send_tool_result(result.model_dump())
                except ValidationError as e:
                    await self.send_error(f"Invalid arguments: {e}")
                except Exception as e:
                    await self.send_error(f"Failed to create group: {e}")
            
            elif name == "get_group_participants":
                # Get group participants
                session_id = arguments.get("session_id") or self.current_session_id
                
                if not session_id:
                    await self.send_error("No active session")
                    return
                
                try:
                    group_participants_args = GroupParticipants.model_validate(arguments)
                    participants = await group.get_group_participants(
                        session_id=session_id,
                        group_id=group_participants_args.group_id
                    )
                    await self.send_tool_result({"participants": [p.model_dump() for p in participants]})
                except ValidationError as e:
                    await self.send_error(f"Invalid arguments: {e}")
                except Exception as e:
                    await self.send_error(f"Failed to get group participants: {e}")
            
            else:
                await self.send_error(f"Unknown tool: {name}")
        
        except Exception as e:
            logger.error(f"Error handling tool call: {e}")
            await self.send_error(f"Error: {str(e)}")
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools."""
        tools = [
            Tool(
                name="list_tools",
                description="List available tools",
                input_schema={}
            ),
            Tool(
                name="create_session",
                description="Create a new WhatsApp session",
                input_schema={
                    "type": "object",
                    "properties": {
                        "session_id": {"type": "string", "description": "ID for the session"}
                    },
                    "required": ["session_id"]
                }
            ),
            Tool(
                name="get_qr_code",
                description="Get a QR code for authentication",
                input_schema={
                    "type": "object",
                    "properties": {
                        "session_id": {"type": "string", "description": "ID of the session"}
                    }
                }
            ),
            Tool(
                name="authenticate",
                description="Authenticate using QR code",
                input_schema={
                    "type": "object",
                    "properties": {
                        "session_id": {"type": "string", "description": "ID of the session"},
                        "qr_code": {"type": "string", "description": "QR code text"}
                    },
                    "required": ["qr_code"]
                }
            ),
            Tool(
                name="logout",
                description="Logout from a session",
                input_schema={
                    "type": "object",
                    "properties": {
                        "session_id": {"type": "string", "description": "ID of the session"}
                    }
                }
            ),
            Tool(
                name="send_message",
                description="Send a message to a chat",
                input_schema=SendMessage.model_json_schema()
            ),
            Tool(
                name="get_chats",
                description="Get a list of chats",
                input_schema={
                    "type": "object",
                    "properties": {
                        "session_id": {"type": "string", "description": "ID of the session"},
                        "limit": {"type": "integer", "description": "Maximum number of chats to return"},
                        "offset": {"type": "integer", "description": "Offset for pagination"}
                    }
                }
            ),
            Tool(
                name="create_group",
                description="Create a new WhatsApp group",
                input_schema=CreateGroup.model_json_schema()
            ),
            Tool(
                name="get_group_participants",
                description="Get the participants of a WhatsApp group",
                input_schema=GroupParticipants.model_json_schema()
            )
        ]
        
        return [tool.model_dump() for tool in tools]
    
    async def send_text(self, text: str):
        """Send a text message."""
        message = MCP_Message(
            type=MCP_MessageType.TEXT,
            content=TextContent(text=text)
        )
        await self.send_message(message)
    
    async def send_tool_result(self, result: Union[Dict[str, Any], List[Dict[str, Any]]]):
        """Send a tool result."""
        message = MCP_Message(
            type=MCP_MessageType.TOOL_RESULT,
            content=result
        )
        await self.send_message(message)
    
    async def send_error(self, error: str):
        """Send an error message."""
        message = MCP_Message(
            type=MCP_MessageType.TOOL_ERROR,
            content=error
        )
        await self.send_message(message)
    
    async def send_message(self, message: MCP_Message):
        """Send a message to the client."""
        # Write the JSON to stdout
        output = json.dumps(message.model_dump())
        print(output, flush=True)


async def main():
    """Run the MCP server."""
    server = MCPServer()
    try:
        await server.handle_input()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())