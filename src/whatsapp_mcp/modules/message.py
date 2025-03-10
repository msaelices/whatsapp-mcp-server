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
    content: Union[TextContent, MediaContent, LocationContent, ContactContent, 
                  ButtonsContent, ListContent, PollContent],
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
        # Prepare the message data based on content type
        message_data = {}
        content_type = getattr(content, "type", "text")
        
        if content_type == "text":
            message_data = {
                "to": chat_id,
                "text": {"body": content.text}
            }
        elif content_type in ("image", "document", "audio", "video", "sticker"):
            message_data = {
                "to": chat_id,
                "type": content_type,
                content_type: {}
            }
            
            # Handle media content
            if content.url:
                message_data[content_type]["link"] = content.url
            elif content.data:
                message_data[content_type]["base64"] = content.data
            
            # Add caption for media if provided
            if hasattr(content, "caption") and content.caption:
                message_data[content_type]["caption"] = content.caption
            
            # Add filename for documents if provided
            if content_type == "document" and content.filename:
                message_data[content_type]["filename"] = content.filename
        elif content_type == "location":
            message_data = {
                "to": chat_id,
                "type": "location",
                "location": {
                    "latitude": content.latitude,
                    "longitude": content.longitude
                }
            }
            
            if content.name:
                message_data["location"]["name"] = content.name
            if content.address:
                message_data["location"]["address"] = content.address
        elif content_type == "contact":
            message_data = {
                "to": chat_id,
                "type": "contacts",
                "contacts": [{
                    "name": {
                        "formatted_name": content.name
                    },
                    "phones": [{
                        "phone": content.phone,
                        "type": "MOBILE"
                    }]
                }]
            }
            
            if content.email:
                message_data["contacts"][0]["emails"] = [{
                    "email": content.email,
                    "type": "WORK"
                }]
        elif content_type == "buttons":
            # Interactive message with buttons
            message_data = {
                "to": chat_id,
                "type": "interactive",
                "interactive": {
                    "type": "button",
                    "body": {
                        "text": content.text
                    },
                    "action": {
                        "buttons": [
                            {
                                "type": "reply",
                                "reply": {
                                    "id": button.id,
                                    "title": button.title
                                }
                            } for button in content.buttons
                        ]
                    }
                }
            }
        elif content_type == "list":
            # Interactive message with list
            message_data = {
                "to": chat_id,
                "type": "interactive",
                "interactive": {
                    "type": "list",
                    "body": {
                        "text": content.text
                    },
                    "action": {
                        "button": content.button_text,
                        "sections": [
                            {
                                "title": section.title,
                                "rows": [
                                    {
                                        "id": item.id,
                                        "title": item.title,
                                        "description": item.description or ""
                                    } for item in section.items
                                ]
                            } for section in content.sections
                        ]
                    }
                }
            }
        elif content_type == "poll":
            # Poll message (may not be directly supported by the API)
            # Implement based on API capabilities
            message_data = {
                "to": chat_id,
                "type": "interactive",
                "interactive": {
                    "type": "button",  # Use button as an alternative
                    "body": {
                        "text": f"Poll: {content.text}\n\n" + "\n".join(
                            f"{i+1}. {option.title}" for i, option in enumerate(content.options)
                        )
                    },
                    "action": {
                        "buttons": [
                            {
                                "type": "reply",
                                "reply": {
                                    "id": option.id,
                                    "title": option.title[:20]  # Button titles are limited
                                }
                            } for option in content.options[:3]  # WhatsApp has a limit on buttons
                        ]
                    }
                }
            }
        
        # Handle reply_to if provided
        if reply_to:
            message_data["context"] = {"message_id": reply_to}
        
        # Send the message via the WhatsApp API
        logger.debug(f"Sending message data: {json.dumps(message_data)}")
        
        # Convert to asyncio to prevent blocking
        response = await asyncio.to_thread(
            whatsapp_client.client.send_message, 
            message_data
        )
        
        # Extract message ID from response
        message_id = response.get("messages", [{}])[0].get("id", f"msg_{uuid.uuid4().hex[:12]}")
        
        result = {
            "message_id": message_id,
            "status": "sent",
            "timestamp": datetime.now().isoformat(),
            "response": response
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