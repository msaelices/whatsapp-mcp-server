"""WhatsApp MCP Server implementation."""

import json
import logging
from enum import Enum
from typing import Optional

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from pydantic import BaseModel, Field, ValidationError

from whatsapp_mcp.models import CreateGroup, GroupParticipants, SendMessage
from whatsapp_mcp.modules import auth, group, message

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class WhatsAppTools(str, Enum):
    """WhatsApp MCP tools."""

    LIST_TOOLS = "list_tools"
    CREATE_SESSION = "create_session"
    SEND_MESSAGE = "send_message"
    GET_CHATS = "get_chats"
    CREATE_GROUP = "create_group"
    GET_GROUP_PARTICIPANTS = "get_group_participants"


class CreateSessionModel(BaseModel):
    """Input schema for create_session tool."""

    pass


class GetChatsModel(BaseModel):
    """Input schema for get_chats tool."""

    limit: int = Field(50, description="Maximum number of chats to return")
    offset: int = Field(0, description="Offset for pagination")


# Global state for the current session
current_session_id: Optional[str] = None


# Define list_tools and call_tool functions outside of serve() to make them testable
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name=WhatsAppTools.CREATE_SESSION,
            description="Create a new WhatsApp session",
            inputSchema=CreateSessionModel.model_json_schema(),
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


async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Call a tool with the given arguments."""
    try:
        match name:
            case WhatsAppTools.CREATE_SESSION:
                # Create a new session
                success, message_text = await auth.auth_manager.create_session()
                if success:
                    return [TextContent(type="text", text=f"Success: {message_text}")]
                else:
                    return [TextContent(type="text", text=f"Error: {message_text}")]

            case WhatsAppTools.SEND_MESSAGE:
                # Send a message

                if not auth.auth_manager.is_authenticated():
                    return [TextContent(type="text", text="Error: No active session")]

                try:
                    send_message_args = SendMessage.model_validate(arguments)
                    result = await message.send_message(
                        phone_number=send_message_args.phone_number,
                        content=send_message_args.content,
                        reply_to=send_message_args.reply_to,
                    )
                    return [TextContent(type="text", text=json.dumps(result))]
                except ValidationError as e:
                    return [
                        TextContent(type="text", text=f"Error: Invalid arguments: {e}")
                    ]
                except Exception as e:
                    return [
                        TextContent(
                            type="text", text=f"Error: Failed to send message: {e}"
                        )
                    ]

            case WhatsAppTools.GET_CHATS:
                # Get chats
                if not auth.auth_manager.is_authenticated():
                    return [TextContent(type="text", text="Error: No active session")]

                limit = arguments.get("limit", 50)
                offset = arguments.get("offset", 0)

                try:
                    chats = await message.get_chats(limit=limit, offset=offset)
                    return [TextContent(type="text", text=json.dumps({"chats": chats}))]
                except Exception as e:
                    return [
                        TextContent(
                            type="text", text=f"Error: Failed to get chats: {e}"
                        )
                    ]

            case WhatsAppTools.CREATE_GROUP:
                # Create a group
                if not auth.auth_manager.is_authenticated():
                    return [TextContent(type="text", text="Error: No active session")]

                try:
                    create_group_args = CreateGroup.model_validate(arguments)
                    group_result = await group.create_group(
                        group_name=create_group_args.group_name,
                        participants=create_group_args.participants,
                    )
                    return [
                        TextContent(
                            type="text", text=json.dumps(group_result.model_dump())
                        )
                    ]
                except ValidationError as e:
                    return [
                        TextContent(type="text", text=f"Error: Invalid arguments: {e}")
                    ]
                except Exception as e:
                    return [
                        TextContent(
                            type="text", text=f"Error: Failed to create group: {e}"
                        )
                    ]

            case WhatsAppTools.GET_GROUP_PARTICIPANTS:
                # Get group participants
                if not auth.auth_manager.is_authenticated():
                    return [TextContent(type="text", text="Error: No active session")]

                try:
                    group_participants_args = GroupParticipants.model_validate(
                        arguments
                    )
                    participants = await group.get_group_participants(
                        group_id=group_participants_args.group_id
                    )
                    return [
                        TextContent(
                            type="text",
                            text=json.dumps(
                                {"participants": [p.model_dump() for p in participants]}
                            ),
                        )
                    ]
                except ValidationError as e:
                    return [
                        TextContent(type="text", text=f"Error: Invalid arguments: {e}")
                    ]
                except Exception as e:
                    return [
                        TextContent(
                            type="text",
                            text=f"Error: Failed to get group participants: {e}",
                        )
                    ]

            case _:
                return [TextContent(type="text", text=f"Error: Unknown tool: {name}")]

    except Exception as e:
        logger.error(f"Error handling tool call: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def serve() -> None:
    """Run the WhatsApp MCP server."""
    logger.info("Starting WhatsApp MCP Server")
    server: Server = Server("whatsapp-mcp")

    @server.list_tools()
    async def server_list_tools() -> list[Tool]:
        """List available tools."""
        return await list_tools()

    @server.call_tool()
    async def server_call_tool(name: str, arguments: dict) -> list[TextContent]:
        """Call a tool with the given arguments."""
        return await call_tool(name, arguments)

    # Run the server
    options = server.create_initialization_options()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, options, raise_exceptions=True)
