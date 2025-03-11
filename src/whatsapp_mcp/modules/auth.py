"""Authentication module for WhatsApp MCP Server."""

import asyncio
import base64
import io
import logging
import os
from typing import Dict, Optional, Tuple, Any

import qrcode
from dotenv import load_dotenv

from whatsapp_mcp.models import QRCode

# Import the WhatsApp API client
from whatsapp_api_client_python.API import GreenApi
from whatsapp_api_client_python.response import Response

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

    async def generate_qr(self) -> Optional[QRCode]:
        """Generate a QR code for authentication."""
        logger.info("Generating QR code")

        if not self.client:
            logger.error("Client not initialized")
            return None

        # Get QR code from the WhatsApp API
        try:
            # Start a new session with the WhatsApp API
            # Initiate QR code generation
            await asyncio.to_thread(lambda: self.client.account.qr())

            # Wait for the QR code to be generated
            qr_code_data = None
            max_retries = 20
            retry_count = 0

            while not qr_code_data and retry_count < max_retries:
                status_response: Response = await asyncio.to_thread(
                    lambda: self.client.account.getStatusInstance()
                )

                # Handle the response from getStatusInstance
                if status_response.code == 200:
                    if status_response.data and "stateInstance" in status_response.data:
                        state = status_response.data["stateInstance"]

                        if state == "authorized":
                            logger.info("Already authorized, no need for QR code")
                            self.is_authenticated = True
                            self.state = "authorized"
                            return None

                        if state == "notAuthorized":
                            # Check if the qrCode field is present in the response
                            if "qrCode" in status_response.data:
                                qr_code_data = status_response.data["qrCode"]
                                logger.info("QR code obtained successfully")
                                break

                if error := status_response.error:
                    logger.warning(f"Error while getting QR code: {error}")

                # Continue trying if we haven't found a QR code yet
                retry_count += 1
                logger.debug(
                    f"Waiting for QR code, attempt {retry_count}/{max_retries}"
                )
                await asyncio.sleep(1)
        except Exception as e:
            logger.error(f"Error generating QR code: {e}")
            return None

        if not qr_code_data:
            logger.error("Failed to get QR code after maximum retries")
            return None

        # Store the QR code data
        self.qr_code = qr_code_data

        # Create a QR code image
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_code_data)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        # Convert to base64
        buffered = io.BytesIO()
        img.save(buffered)
        img_str = base64.b64encode(buffered.getvalue()).decode("ascii")

        return QRCode(data=img_str, code=qr_code_data)


class AuthManager:
    """Manager for authentication-related operations."""

    def __init__(self) -> None:
        self.session: WhatsAppClient | None = None

    async def create_session(self) -> Tuple[bool, str]:
        """Create a new session."""
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
