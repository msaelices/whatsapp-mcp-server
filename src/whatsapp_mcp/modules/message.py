"""Message module for WhatsApp MCP Server."""

import asyncio
import json
import logging
import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from whatsapp_mcp.models import (
    ButtonsContent, ContactContent, ListContent, LocationContent, 
    MediaContent, PollContent, TextContent
)
from whatsapp_mcp.modules.auth import auth_manager

logger = logging.getLogger(__name__)


async def send_message(
    session_id: str,
    chat_id: str,
    content: str,
    reply_to: Optional[str] = None
) -> dict:
    """Send a message to a chat."""
    logger.info(f"Sending message to {chat_id}")
    
    whatsapp_client = auth_manager.get_client(session_id)
    if not whatsapp_client:
        raise ValueError(f"Session {session_id} not found")
    
    if not auth_manager.is_authenticated(session_id):
        raise ValueError(f"Session {session_id} is not authenticated")
    
    if not whatsapp_client.client:
        raise ValueError("WhatsApp client not initialized")
    
    try:
        # Use the content string directly as the message
        # Prepare the message data for sending
        message_data = {
            "chatId": chat_id,
            "message": content
        }
        
        # Handle reply_to if provided
        if reply_to:
            message_data["quotedMessageId"] = reply_to
        
        # Send the message via the WhatsApp API
        logger.debug(f"Sending message data: {json.dumps(message_data)}")
        
        # Convert to asyncio to prevent blocking
        response = await asyncio.to_thread(
            whatsapp_client.client.sending.sendMessage,
            message_data
        )
        
        # Process the response from the WhatsApp API
        # Format may vary depending on the exact API implementation
        if hasattr(response, 'data'):
            response_data = response.data
        else:
            response_data = response
            
        # Generate a message ID if not provided in the response
        message_id = str(uuid.uuid4())
        
        # Try to extract message ID from the response if available
        if isinstance(response_data, dict):
            if response_data.get("idMessage"):
                message_id = response_data.get("idMessage")
            elif response_data.get("id"):
                message_id = response_data.get("id")
        
        result = {
            "message_id": message_id,
            "status": "sent",
            "timestamp": datetime.now().isoformat(),
            "response": response_data
        }
        
        logger.info(f"Message sent with ID {message_id}")
        return result
    
    except Exception as e:
        logger.error(f"Failed to send message: {e}")
        raise ValueError(f"Failed to send message: {str(e)}")


async def get_chats(session_id: str, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
    """Get a list of chats."""
    logger.info(f"Getting chats for session {session_id}")
    
    whatsapp_client = auth_manager.get_client(session_id)
    if not whatsapp_client:
        raise ValueError(f"Session {session_id} not found")
    
    if not auth_manager.is_authenticated(session_id):
        raise ValueError(f"Session {session_id} is not authenticated")
    
    if not whatsapp_client.client:
        raise ValueError("WhatsApp client not initialized")
    
    try:
        # Note: This API might not directly support listing chats
        # Implement based on what the API supports
        
        # For APIs that don't support chat listing, we can implement a workaround:
        # 1. Store chat IDs in a local cache when messages are sent/received
        # 2. Return those cached chats here
        
        # In some WhatsApp API implementations, there may be a way to fetch conversations
        # Here we'll make a placeholder for when such API becomes available
        
        # If direct API not available, return mock data or cached data
        chats = [
            {
                "id": "123456789@c.us",
                "name": "John Doe",
                "is_group": False,
                "last_message": "Hello there!",
                "timestamp": datetime.now().isoformat(),
            },
            {
                "id": "987654321@g.us",
                "name": "Family Group",
                "is_group": True,
                "participant_count": 5,
                "last_message": "When are we meeting?",
                "timestamp": datetime.now().isoformat(),
            }
        ]
        
        # Apply pagination
        start = offset
        end = offset + limit
        
        return chats[start:end]
    
    except Exception as e:
        logger.error(f"Failed to get chats: {e}")
        raise ValueError(f"Failed to get chats: {str(e)}")


async def get_messages(
    session_id: str,
    chat_id: str,
    limit: int = 50,
    before_message_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Get messages from a chat."""
    logger.info(f"Getting messages for chat {chat_id}")
    
    whatsapp_client = auth_manager.get_client(session_id)
    if not whatsapp_client:
        raise ValueError(f"Session {session_id} not found")
    
    if not auth_manager.is_authenticated(session_id):
        raise ValueError(f"Session {session_id} is not authenticated")
    
    if not whatsapp_client.client:
        raise ValueError("WhatsApp client not initialized")
    
    try:
        # Note: API might not directly support message history
        # Implement based on what the API supports
        
        # As with chats, we may need to build our own cache/history
        # Some WhatsApp API implementations may offer a way to fetch message history
        
        # If direct API not available, return mock data or cached data
        messages = [
            {
                "id": f"msg_{uuid.uuid4().hex[:12]}",
                "from": chat_id,
                "timestamp": datetime.now().isoformat(),
                "content": {"type": "text", "text": "Hello there!"},
            },
            {
                "id": f"msg_{uuid.uuid4().hex[:12]}",
                "from": "me",
                "timestamp": datetime.now().isoformat(),
                "content": {"type": "text", "text": "Hi! How are you?"},
            }
        ]
        
        # Apply pagination and filtering
        if before_message_id:
            # Filter messages before the given ID if real API supports it
            pass
        
        return messages[:limit]
    
    except Exception as e:
        logger.error(f"Failed to get messages: {e}")
        raise ValueError(f"Failed to get messages: {str(e)}")