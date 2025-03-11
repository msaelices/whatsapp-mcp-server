"""Group module for WhatsApp MCP Server."""

import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from whatsapp_mcp.models import Contact, Group, Participant
from whatsapp_mcp.modules.auth import auth_manager

logger = logging.getLogger(__name__)


async def create_group(group_name: str, participants: List[str]) -> Group:
    """Create a new WhatsApp group."""
    logger.info(f"Creating group {group_name} with {len(participants)} participants")

    whatsapp_client = auth_manager.get_client()
    if not whatsapp_client:
        raise ValueError("Session not found")

    if not whatsapp_client.client:
        raise ValueError("WhatsApp client not initialized")

    if len(participants) < 1:
        raise ValueError("Need at least one participant to create a group")

    try:
        # Format participant phone numbers correctly
        formatted_participants = []
        for phone in participants:
            # Add @c.us suffix if not already present
            if not phone.endswith("@c.us"):
                formatted_phone = f"{phone}@c.us"
            else:
                formatted_phone = phone
            formatted_participants.append(formatted_phone)

        # Prepare the request data for group creation
        # Note: The exact API format may vary depending on the WhatsApp API being used
        group_data = {"group_name": group_name, "participants": formatted_participants}

        logger.debug(f"Creating group with data: {json.dumps(group_data)}")

        # Create the group via the WhatsApp API
        # The response format may vary depending on the API
        response = await asyncio.to_thread(
            whatsapp_client.client.create_group, group_data
        )

        # Parse the response
        if not response or not response.get("success", False):
            error_msg = (
                response.get("error", "Unknown error") if response else "No response"
            )
            logger.error(f"Failed to create group: {error_msg}")
            raise ValueError(f"Failed to create group: {error_msg}")

        # Extract group information from response
        group_info = response.get("group", {})
        group_id = group_info.get("id", f"{uuid.uuid4().hex[:12]}@g.us")

        # Create participant objects
        participant_objects = []
        for i, phone in enumerate(participants):
            contact = Contact(
                id=formatted_participants[i],
                name=f"Participant {i + 1}",  # We may not have names initially
                phone=phone,
            )
            participant = Participant(id=contact.id, is_admin=False, contact=contact)
            participant_objects.append(participant)

        # Create the group object
        group = Group(
            id=group_id,
            name=group_name,
            description=group_info.get("description", ""),
            owner=group_info.get("owner", "me"),
            creation_time=datetime.now().isoformat(),
            participants=participant_objects,
        )

        logger.info(f"Group created with ID {group_id}")
        return group

    except Exception as e:
        logger.error(f"Failed to create group: {e}")
        raise ValueError(f"Failed to create group: {str(e)}")


async def get_group_participants(group_id: str) -> List[Participant]:
    """Get the participants of a WhatsApp group."""
    logger.info(f"Getting participants for group {group_id}")

    whatsapp_client = auth_manager.get_client()
    if not whatsapp_client:
        raise ValueError("Session not found")

    if not whatsapp_client.client:
        raise ValueError("WhatsApp client not initialized")

    # Validate group ID format
    if not group_id.endswith("@g.us"):
        raise ValueError("Invalid group ID format. Must end with @g.us")

    try:
        # Prepare the request data for fetching group participants
        request_data = {"group_id": group_id}

        logger.debug(f"Fetching participants for group: {group_id}")

        # Get the participants via the WhatsApp API
        response = await asyncio.to_thread(
            whatsapp_client.client.get_group_participants, request_data
        )

        # Parse the response
        if not response or not response.get("success", False):
            error_msg = (
                response.get("error", "Unknown error") if response else "No response"
            )
            logger.error(f"Failed to get group participants: {error_msg}")
            raise ValueError(f"Failed to get group participants: {error_msg}")

        # Extract participants information from response
        participants_info = response.get("participants", [])

        # Create participant objects
        participants = []
        for p_info in participants_info:
            p_id = p_info.get("id", "")
            p_name = p_info.get("name", "Unknown")
            p_phone = p_info.get("phone", p_id.replace("@c.us", ""))
            p_is_admin = p_info.get("is_admin", False)

            contact = Contact(id=p_id, name=p_name, phone=p_phone)

            participant = Participant(id=p_id, is_admin=p_is_admin, contact=contact)

            participants.append(participant)

        return participants

    except Exception as e:
        logger.error(f"Failed to get group participants: {e}")
        raise ValueError(f"Failed to get group participants: {str(e)}")


async def add_participant(group_id: str, participant_phone: str) -> Dict[str, Any]:
    """Add a participant to a WhatsApp group."""
    logger.info(f"Adding participant {participant_phone} to group {group_id}")

    whatsapp_client = auth_manager.get_client()
    if not whatsapp_client:
        raise ValueError("Session not found")

    if not whatsapp_client.client:
        raise ValueError("WhatsApp client not initialized")

    # Validate group ID format
    if not group_id.endswith("@g.us"):
        raise ValueError("Invalid group ID format. Must end with @g.us")

    try:
        # Format participant phone number correctly
        if not participant_phone.endswith("@c.us"):
            formatted_phone = f"{participant_phone}@c.us"
        else:
            formatted_phone = participant_phone

        # Prepare the request data
        request_data = {"group_id": group_id, "participant": formatted_phone}

        logger.debug(f"Adding participant with data: {json.dumps(request_data)}")

        # Add the participant via the WhatsApp API
        response = await asyncio.to_thread(
            whatsapp_client.client.add_group_participant, request_data
        )

        # Parse the response
        if not response or not response.get("success", False):
            error_msg = (
                response.get("error", "Unknown error") if response else "No response"
            )
            logger.error(f"Failed to add participant: {error_msg}")
            raise ValueError(f"Failed to add participant: {error_msg}")

        return {
            "success": True,
            "group_id": group_id,
            "participant": formatted_phone,
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to add participant: {e}")
        raise ValueError(f"Failed to add participant: {str(e)}")


async def remove_participant(group_id: str, participant_id: str) -> Dict[str, Any]:
    """Remove a participant from a WhatsApp group."""
    logger.info(f"Removing participant {participant_id} from group {group_id}")

    whatsapp_client = auth_manager.get_client()
    if not whatsapp_client:
        raise ValueError("Session not found")

    if not whatsapp_client.client:
        raise ValueError("WhatsApp client not initialized")

    # Validate group ID format
    if not group_id.endswith("@g.us"):
        raise ValueError("Invalid group ID format. Must end with @g.us")

    # Validate participant ID format
    if not participant_id.endswith("@c.us"):
        raise ValueError("Invalid participant ID format. Must end with @c.us")

    try:
        # Prepare the request data
        request_data = {"group_id": group_id, "participant": participant_id}

        logger.debug(f"Removing participant with data: {json.dumps(request_data)}")

        # Remove the participant via the WhatsApp API
        response = await asyncio.to_thread(
            whatsapp_client.client.remove_group_participant, request_data
        )

        # Parse the response
        if not response or not response.get("success", False):
            error_msg = (
                response.get("error", "Unknown error") if response else "No response"
            )
            logger.error(f"Failed to remove participant: {error_msg}")
            raise ValueError(f"Failed to remove participant: {error_msg}")

        return {
            "success": True,
            "group_id": group_id,
            "participant": participant_id,
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to remove participant: {e}")
        raise ValueError(f"Failed to remove participant: {str(e)}")


async def update_group_settings(
    group_id: str,
    name: Optional[str] = None,
    description: Optional[str] = None,
) -> Dict[str, Any]:
    """Update the settings of a WhatsApp group."""
    logger.info(f"Updating settings for group {group_id}")

    whatsapp_client = auth_manager.get_client()
    if not whatsapp_client:
        raise ValueError("Session not found")

    if not whatsapp_client.client:
        raise ValueError("WhatsApp client not initialized")

    # Validate group ID format
    if not group_id.endswith("@g.us"):
        raise ValueError("Invalid group ID format. Must end with @g.us")

    # Ensure at least one setting is being updated
    if name is None and description is None:
        raise ValueError("Must provide at least one setting to update")

    try:
        # Prepare the request data
        request_data = {"group_id": group_id}

        if name is not None:
            request_data["name"] = name
        if description is not None:
            request_data["description"] = description

        logger.debug(f"Updating group settings with data: {json.dumps(request_data)}")

        # Update the group settings via the WhatsApp API
        response = await asyncio.to_thread(
            whatsapp_client.client.update_group_settings, request_data
        )

        # Parse the response
        if not response or not response.get("success", False):
            error_msg = (
                response.get("error", "Unknown error") if response else "No response"
            )
            logger.error(f"Failed to update group settings: {error_msg}")
            raise ValueError(f"Failed to update group settings: {error_msg}")

        updated_fields = []
        if name is not None:
            updated_fields.append("name")
        if description is not None:
            updated_fields.append("description")

        return {
            "success": True,
            "group_id": group_id,
            "updated_fields": updated_fields,
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to update group settings: {e}")
        raise ValueError(f"Failed to update group settings: {str(e)}")

