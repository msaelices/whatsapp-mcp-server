"""Models for WhatsApp MCP Server."""

from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


class MCP_MessageType(str, Enum):
    TEXT = "text"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    TOOL_ERROR = "tool_error"


class TextContent(BaseModel):
    """Text content for messages."""
    type: str = "text"
    text: str


class MediaType(str, Enum):
    """Types of media that can be sent."""
    IMAGE = "image"
    DOCUMENT = "document"
    AUDIO = "audio"
    VIDEO = "video"
    STICKER = "sticker"


class MediaContent(BaseModel):
    """Media content for messages."""
    type: MediaType
    url: Optional[str] = None
    mimetype: Optional[str] = None
    filename: Optional[str] = None
    caption: Optional[str] = None
    data: Optional[str] = None  # Base64 encoded data


class LocationContent(BaseModel):
    """Location content for messages."""
    type: str = "location"
    latitude: float
    longitude: float
    name: Optional[str] = None
    address: Optional[str] = None


class ContactContent(BaseModel):
    """Contact content for messages."""
    type: str = "contact"
    name: str
    phone: str
    email: Optional[str] = None


class Button(BaseModel):
    """Button for interactive messages."""
    id: str
    title: str


class ButtonsContent(BaseModel):
    """Buttons content for interactive messages."""
    type: str = "buttons"
    text: str
    buttons: List[Button]


class ListItem(BaseModel):
    """Item for list messages."""
    id: str
    title: str
    description: Optional[str] = None


class ListSection(BaseModel):
    """Section for list messages."""
    title: str
    items: List[ListItem]


class ListContent(BaseModel):
    """List content for interactive messages."""
    type: str = "list"
    text: str
    button_text: str
    sections: List[ListSection]


class PollOption(BaseModel):
    """Option for poll messages."""
    id: str
    title: str


class PollContent(BaseModel):
    """Poll content for interactive messages."""
    type: str = "poll"
    text: str
    options: List[PollOption]
    allow_multiple_answers: bool = False


class SendMessage(BaseModel):
    """Input schema for send_message tool."""
    chat_id: str = Field(..., description="The WhatsApp ID of the chat to send the message to")
    content: Union[TextContent, MediaContent, LocationContent, ContactContent, 
                  ButtonsContent, ListContent, PollContent] = Field(
        ..., description="The content of the message to send"
    )
    reply_to: Optional[str] = Field(None, description="ID of the message to reply to")


class CreateGroup(BaseModel):
    """Input schema for create_group tool."""
    group_name: str = Field(..., description="Name of the group to create")
    participants: List[str] = Field(..., description="List of participant phone numbers")


class GroupParticipants(BaseModel):
    """Input schema for get_group_participants tool."""
    group_id: str = Field(..., description="The WhatsApp ID of the group")


class Contact(BaseModel):
    """Model for a WhatsApp contact."""
    id: str
    name: Optional[str] = None
    short_name: Optional[str] = None
    push_name: Optional[str] = None
    phone: str


class Chat(BaseModel):
    """Model for a WhatsApp chat."""
    id: str
    name: Optional[str] = None
    is_group: bool
    participants: Optional[List[Contact]] = None


class Group(BaseModel):
    """Model for a WhatsApp group."""
    id: str
    name: str
    description: Optional[str] = None
    owner: Optional[str] = None
    creation_time: Optional[str] = None
    participants: List[Contact]


class Participant(BaseModel):
    """Model for a group participant."""
    id: str
    is_admin: bool = False
    contact: Contact


class Tool(BaseModel):
    """Schema for tool definition."""
    name: str
    description: str
    input_schema: Dict[str, Any]


class ToolCall(BaseModel):
    """Schema for tool call."""
    name: str
    arguments: Dict[str, Any]


class MCP_Message(BaseModel):
    """Schema for MCP messages."""
    type: MCP_MessageType
    content: Optional[Union[TextContent, ToolCall, Dict[str, Any], str]] = None


class QRCode(BaseModel):
    """QR Code for authentication."""
    data: str  # Base64 encoded image
    code: str  # The actual QR code text