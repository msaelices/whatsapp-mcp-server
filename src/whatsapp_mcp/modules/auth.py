"""Authentication module for WhatsApp MCP Server."""

import logging
import os
from typing import Dict, Tuple, Any

from dotenv import load_dotenv


# Import the WhatsApp API client
from whatsapp_api_client_python.API import GreenApi

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class WhatsAppClient:
    """WhatsApp client implementation using whatsapp-api-client-python."""

    def __init__(self) -> None:
        self.is_authenticated = False
        self.session_data: Dict[str, Any] = {}
        self.client = None
        self.qr_code = None
        self.state = "DISCONNECTED"

    async def initialize(self) -> bool:
        """Initialize the client."""
        logger.info("Initializing WhatsApp client")
        try:
            # Initialize the WhatsApp API client with GreenAPI credentials from environment variables
            id_instance = os.getenv("GREENAPI_ID_INSTANCE")
            api_token_instance = os.getenv("GREENAPI_API_TOKEN")

            if not id_instance or not api_token_instance:
                logger.error(
                    "Missing required environment variables: GREENAPI_ID_INSTANCE or GREENAPI_API_TOKEN"
                )
                return False

            self.client = GreenApi(
                idInstance=id_instance, apiTokenInstance=api_token_instance
            )
            return True
        except Exception as e:
            logger.error(f"Failed to initialize WhatsApp client: {e}")
            return False


class AuthManager:
    """Manager for authentication-related operations."""

    def __init__(self) -> None:
        self.session: WhatsAppClient | None = None

    async def open_session(self) -> Tuple[bool, str]:
        """Open a new session."""
        if self.session:
            return False, "Session already exists"

        client = WhatsAppClient()
        success = await client.initialize()

        if success:
            self.session = client
            return True, "Session created successfully"

        return False, "Failed to create session"

    def is_authenticated(self) -> bool:
        """Check if a session is authenticated."""
        return self.session is not None

    def get_client(self) -> WhatsAppClient | None:
        """Get the client for a session."""
        return self.session


# Create a singleton instance
auth_manager = AuthManager()
