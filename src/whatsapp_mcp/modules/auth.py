"""Authentication module for WhatsApp MCP Server."""

import asyncio
import base64
import io
import json
import logging
import os
import time
from typing import Dict, Optional, Tuple, Any

import qrcode
from dotenv import load_dotenv

from whatsapp_mcp.models import QRCode

# Import the WhatsApp API client
from whatsapp_api_client_python import API

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class WhatsAppClient:
    """WhatsApp client implementation using whatsapp-api-client-python."""

    def __init__(self):
        self.is_authenticated = False
        self.session_data = {}
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
                logger.error("Missing required environment variables: GREENAPI_ID_INSTANCE or GREENAPI_API_TOKEN")
                return False
                
            self.client = API(idInstance=id_instance, apiTokenInstance=api_token_instance)
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

        # Start a new session with the WhatsApp API
        response = await asyncio.to_thread(self.client.start_session)

        # Wait for the QR code to be generated
        qr_code_data = None
        max_retries = 20
        retry_count = 0

        while not qr_code_data and retry_count < max_retries:
            status_data = await asyncio.to_thread(self.client.get_status_session)

            if status_data and "state" in status_data:
                self.state = status_data["state"]

                if self.state == "CONNECTED":
                    self.is_authenticated = True
                    logger.info("Client already authenticated")
                    return None

                if self.state == "STARTING" and "qrCode" in status_data:
                    qr_code_data = status_data["qrCode"]
                    break

            retry_count += 1
            await asyncio.sleep(1)

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

    async def authenticate_qr(self, qr_code: str) -> bool:
        """Authenticate using QR code.

        In the WhatsApp API, authentication happens automatically when the
        user scans the QR code with their phone. This method checks the
        authentication status.
        """
        logger.info("Checking authentication status")

        if not self.client:
            logger.error("Client not initialized")
            return False

        try:
            # Check the status of the session
            max_retries = 30
            retry_count = 0

            while retry_count < max_retries:
                status_data = await asyncio.to_thread(self.client.get_status_session)

                if status_data and "state" in status_data:
                    self.state = status_data["state"]

                    if self.state == "CONNECTED":
                        self.is_authenticated = True
                        # Store session data for restoration
                        self.session_data = {
                            "session_id": status_data.get("session", ""),
                            "authenticated_at": time.time(),
                            "state": self.state,
                        }
                        logger.info("Authentication successful")
                        return True

                    if self.state == "FAILED":
                        logger.error("Authentication failed")
                        return False

                retry_count += 1
                await asyncio.sleep(1)

            logger.error("Authentication timed out")
            return False

        except Exception as e:
            logger.error(f"Failed to authenticate: {e}")
            return False

    async def logout(self) -> bool:
        """Logout from WhatsApp."""
        logger.info("Logging out")

        if not self.client:
            logger.error("Client not initialized")
            return False

        try:
            # Close the session
            response = await asyncio.to_thread(self.client.logout_session)
            self.is_authenticated = False
            self.state = "DISCONNECTED"
            self.session_data = {}
            return True
        except Exception as e:
            logger.error(f"Failed to logout: {e}")
            return False

    async def check_status(self) -> Dict[str, Any]:
        """Check the status of the WhatsApp session."""
        if not self.client:
            return {"state": "DISCONNECTED", "error": "Client not initialized"}

        try:
            status_data = await asyncio.to_thread(self.client.get_status_session)
            if status_data and "state" in status_data:
                self.state = status_data["state"]
                self.is_authenticated = self.state == "CONNECTED"
            return status_data or {"state": "UNKNOWN"}
        except Exception as e:
            logger.error(f"Failed to check status: {e}")
            return {"state": "ERROR", "error": str(e)}


class AuthManager:
    """Manager for authentication-related operations."""

    def __init__(self):
        self.sessions: Dict[str, WhatsAppClient] = {}
        self.session_path = os.path.join(
            os.path.expanduser("~"), ".whatsapp-mcp-sessions"
        )
        self._ensure_session_dir()

    def _ensure_session_dir(self):
        """Ensure the session directory exists."""
        os.makedirs(self.session_path, exist_ok=True)

    def _get_session_file(self, session_id: str) -> str:
        """Get the path to the session file."""
        return os.path.join(self.session_path, f"{session_id}.json")

    async def create_session(self, session_id: str) -> Tuple[bool, str]:
        """Create a new session."""
        if session_id in self.sessions:
            return False, "Session already exists"

        client = WhatsAppClient()
        success = await client.initialize()

        if success:
            self.sessions[session_id] = client
            return True, "Session created successfully"

        return False, "Failed to create session"

    async def get_qr_code(self, session_id: str) -> Optional[QRCode]:
        """Get a QR code for authentication."""
        if session_id not in self.sessions:
            return None

        client = self.sessions[session_id]
        return await client.generate_qr()

    async def authenticate(self, session_id: str, qr_code: str) -> bool:
        """Authenticate a session using a QR code."""
        if session_id not in self.sessions:
            return False

        client = self.sessions[session_id]
        success = await client.authenticate_qr(qr_code)

        if success:
            # Save session data
            with open(self._get_session_file(session_id), "w") as f:
                json.dump(client.session_data, f)

        return success

    async def logout(self, session_id: str) -> bool:
        """Logout from a session."""
        if session_id not in self.sessions:
            return False

        client = self.sessions[session_id]
        success = await client.logout()

        if success:
            # Remove session data
            session_file = self._get_session_file(session_id)
            if os.path.exists(session_file):
                os.remove(session_file)

            # Remove from active sessions
            del self.sessions[session_id]

        return success

    async def restore_session(self, session_id: str) -> bool:
        """Restore a saved session."""
        session_file = self._get_session_file(session_id)

        if not os.path.exists(session_file):
            return False

        try:
            with open(session_file, "r") as f:
                session_data = json.load(f)

            client = WhatsAppClient()
            success = await client.initialize()

            if not success:
                return False

            # Restore the session state from saved data
            client.session_data = session_data
            client.state = session_data.get("state", "DISCONNECTED")
            client.is_authenticated = client.state == "CONNECTED"

            # Verify the session is still valid
            status = await client.check_status()
            if status.get("state") != "CONNECTED":
                logger.warning(
                    f"Session {session_id} no longer valid, need to reauthenticate"
                )
                return False

            self.sessions[session_id] = client
            return True
        except Exception as e:
            logger.error(f"Failed to restore session: {e}")
            return False

    async def check_session_status(self, session_id: str) -> Dict[str, Any]:
        """Check the status of a session."""
        if session_id not in self.sessions:
            return {"success": False, "error": "Session not found"}

        client = self.sessions[session_id]
        status = await client.check_status()
        return {"success": True, "status": status}

    def is_authenticated(self, session_id: str) -> bool:
        """Check if a session is authenticated."""
        if session_id not in self.sessions:
            return False

        return self.sessions[session_id].is_authenticated

    def get_client(self, session_id: str) -> Optional[WhatsAppClient]:
        """Get the client for a session."""
        return self.sessions.get(session_id)


# Create a singleton instance
auth_manager = AuthManager()

