"""Message module for WhatsApp MCP Server."""

import asyncio
import logging
import uuid
from typing import List, Optional, Union

from whatsapp_mcp.models import (
    ButtonsContent, ContactContent, ListContent, LocationContent, 
    MediaContent, PollContent, TextContent
)
from whatsapp_mcp.modules.auth import auth_manager

logger = logging.getLogger(__name__)


async def send_message(
    session_id: str,
    chat_id: str,
    content: Union[TextContent, MediaContent, LocationContent, ContactContent, 
                  ButtonsContent, ListContent, PollContent],
    reply_to: Optional[str] = None
) -> dict:
    """Send a message to a chat."""
    logger.info(f"Sending message to {chat_id}")
    
    client = auth_manager.get_client(session_id)
    if not client:
        raise ValueError(f"Session {session_id} not found")
    
    if not auth_manager.is_authenticated(session_id):
        raise ValueError(f"Session {session_id} is not authenticated")
    
    # Simulate sending different types of messages
    await asyncio.sleep(0.5)  # Simulate network request
    
    message_id = f"msg_{uuid.uuid4().hex[:12]}"
    
    # In a real implementation, we would send the message via the WhatsApp API
    content_type = getattr(content, "type", "text")
    
    response = {
        "message_id": message_id,
        "status": "sent",
        "timestamp": "2023-04-05T12:34:56Z",  # Would be real timestamp in production
    }
    
    logger.info(f"Message sent with ID {message_id}")
    return response


async def get_chats(session_id: str, limit: int = 50, offset: int = 0) -> List[dict]:
    """Get a list of chats."""
    logger.info(f"Getting chats for session {session_id}")
    
    client = auth_manager.get_client(session_id)
    if not client:
        raise ValueError(f"Session {session_id} not found")
    
    if not auth_manager.is_authenticated(session_id):
        raise ValueError(f"Session {session_id} is not authenticated")
    
    # In a real implementation, we would fetch chats from the WhatsApp API
    await asyncio.sleep(0.5)  # Simulate network request
    
    # Mock chat data
    chats = [
        {
            "id": "123456789@c.us",
            "name": "John Doe",
            "is_group": False,
            "last_message": "Hello there!",
            "timestamp": "2023-04-05T12:30:00Z",
        },
        {
            "id": "987654321@g.us",
            "name": "Family Group",
            "is_group": True,
            "participant_count": 5,
            "last_message": "When are we meeting?",
            "timestamp": "2023-04-05T12:15:00Z",
        }
    ]
    
    # Apply pagination
    start = offset
    end = offset + limit
    
    return chats[start:end]


async def get_messages(
    session_id: str,
    chat_id: str,
    limit: int = 50,
    before_message_id: Optional[str] = None
) -> List[dict]:
    """Get messages from a chat."""
    logger.info(f"Getting messages for chat {chat_id}")
    
    client = auth_manager.get_client(session_id)
    if not client:
        raise ValueError(f"Session {session_id} not found")
    
    if not auth_manager.is_authenticated(session_id):
        raise ValueError(f"Session {session_id} is not authenticated")
    
    # In a real implementation, we would fetch messages from the WhatsApp API
    await asyncio.sleep(0.7)  # Simulate network request
    
    # Mock message data
    messages = [
        {
            "id": "msg_1234abcd5678",
            "from": "123456789@c.us",
            "timestamp": "2023-04-05T12:30:00Z",
            "content": {"type": "text", "text": "Hello there!"},
        },
        {
            "id": "msg_5678efgh1234",
            "from": "me",
            "timestamp": "2023-04-05T12:31:00Z",
            "content": {"type": "text", "text": "Hi! How are you?"},
        }
    ]
    
    # Apply pagination and filtering
    if before_message_id:
        # In a real implementation, would filter messages before the given ID
        pass
    
    return messages[:limit]