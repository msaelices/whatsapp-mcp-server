"""Models for WhatsApp MCP Server."""

from enum import Enum
from typing import Any, Dict, List, Union

from pydantic import BaseModel, Field


class CreateSessionModel(BaseModel):
    """Input schema for open_session tool."""

    pass


class GetChatsModel(BaseModel):
    """Input schema for get_chats tool."""

    limit: int = Field(50, description="Maximum number of chats to return")
    offset: int = Field(0, description="Offset for pagination")


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
    url: str | None = None
    mimetype: str | None = None
    filename: str | None = None
    caption: str | None = None
    data: str | None = None  # Base64 encoded data


class LocationContent(BaseModel):
    """Location content for messages."""

    type: str = "location"
    latitude: float
    longitude: float
    name: str | None = None
    address: str | None = None


class ContactContent(BaseModel):
    """Contact content for messages."""

    type: str = "contact"
    name: str
    phone: str
    email: str | None = None


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
    description: str | None = None


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

    phone_number: str = Field(..., description="The phone number of the recipient")
    content: str = Field(..., description="The content of the message to send")
    reply_to: str | None = Field(None, description="ID of the message to reply to")


class CreateGroup(BaseModel):
    """Input schema for create_group tool."""

    group_name: str = Field(..., description="Name of the group to create")
    participants: List[str] = Field(
        ..., description="List of participant phone numbers"
    )


class GroupParticipants(BaseModel):
    """Input schema for get_group_participants tool."""

    group_id: str = Field(..., description="The WhatsApp ID of the group")


class Contact(BaseModel):
    """Model for a WhatsApp contact."""

    id: str
    name: str | None = None
    short_name: str | None = None
    push_name: str | None = None
    phone: str


class Chat(BaseModel):
    """Model for a WhatsApp chat."""

    id: str
    name: str | None = None
    is_group: bool
    participants: List[Contact] | None = None


class Group(BaseModel):
    """Model for a WhatsApp group."""

    id: str
    name: str
    description: str | None = None
    owner: str | None = None
    creation_time: str | None = None
    participants: List[Union[Contact, "Participant"]]


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
    content: TextContent | ToolCall | dict[str, Any] | str | None = None
