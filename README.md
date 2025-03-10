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

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/whatsapp-mcp-server.git
cd whatsapp-mcp-server

# Install dependencies
pip install -e .
```

## Usage

Run the MCP server:

```bash
python src/main.py
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
# Basic syntax
$ claude mcp add <name> <command> [args...]

# Example: Adding the WhatsApp MCP server
$ claude mcp add whatsapp -- python /path/to/src/main.py
```

Then you can interact with it in Claude with commands like:

```
/tool whatsapp create_session --session_id my_session
/tool whatsapp get_qr_code
/tool whatsapp send_message --chat_id "1234567890@c.us" --content '{"type":"text","text":"Hello"}'
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

## License

This project is licensed under the MIT License - see the LICENSE file for details.