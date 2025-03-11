# WhatsApp MCP Server

A server that provides a Model Context Protocol (MCP) interface to interact with WhatsApp Business API.

## Introduction

WhatsApp MCP Server is a Python implementation that enables language models like Claude to interact with WhatsApp functionality through a standardized protocol. It provides capabilities for:

- Authentication via QR code
- Sending various types of messages (text, media, locations, etc.)
- Managing WhatsApp groups
- Listing chats and contacts

## Features

- **Authentication**: Authenticate with WhatsApp using QR code scanning
- **Messaging**: Send text, media, interactive, and location messages
- **Group Management**: Create groups, list members, add/remove participants
- **Session Management**: Create, restore, and manage multiple WhatsApp sessions

## WhatsApp API Client

This project uses the `whatsapp-api-client-python` library to interact with WhatsApp. The client provides access to the WhatsApp Cloud API, which requires:

1. A WhatsApp Business Account
2. A valid API key or access token

You should set up your WhatsApp Business API credentials before using this MCP server. Please refer to the [WhatsApp Business API documentation](https://developers.facebook.com/docs/whatsapp/cloud-api) for more information on how to obtain the necessary credentials.

### Environment Variables

This project uses environment variables for configuration:

- `GREENAPI_ID_INSTANCE`: Your GreenAPI ID instance
- `GREENAPI_API_TOKEN`: Your GreenAPI API token

You can either set these in your environment or use the provided `.env` file (see Installation instructions).

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/whatsapp-mcp-server.git
cd whatsapp-mcp-server

# Install dependencies
pip install -e .

# Set up environment variables
cp .env-template .env
# Edit the .env file with your GreenAPI credentials
```

## Usage

Run the MCP server:

```bash
# Install the package with development mode
pip install -e .

# Run the MCP server
whatsapp-mcp
```

For debugging:

```bash
whatsapp-mcp --debug
```

The server communicates through standard input/output streams using the Model Context Protocol (MCP).

### Available Tools

- `create_session`: Create a new WhatsApp session
- `get_qr_code`: Get a QR code for authentication
- `authenticate`: Authenticate using a QR code
- `logout`: Logout from a session
- `send_message`: Send a message to a chat
- `get_chats`: Get a list of chats
- `create_group`: Create a new WhatsApp group
- `get_group_participants`: Get the participants of a group

## How to add it to Claude Code

To add a WhatsApp server to Claude, use the `claude mcp add` command:

```
# Add the WhatsApp MCP server
$ claude mcp add whatsapp -- python /path/to/src/main.py

# List existing MCP servers - Validate that the server is running
claude mcp list

# Start claude code
claude
```

## Using with Claude

Once the WhatsApp MCP server is running, you can interact with it using Claude in your conversations:

### Authenticating with WhatsApp

```
Login to WhatsApp
```


### Sending a message

```
Send the "Hello" message to John Doe
```

## Development

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run linting
flake8 src/

# Run type checking
mypy src/
```

The setup.py file reads requirements from:
- `requirements.txt` - Core dependencies for running the application
- `dev-requirements.txt` - Additional dependencies for development and testing

## License

This project is licensed under the MIT License - see the LICENSE file for details.
