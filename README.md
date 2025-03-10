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

The server communicates through standard input/output streams using JSON messages following the MCP protocol.

### Example interaction

To list available tools:

```json
{"type": "tool_call", "content": {"name": "list_tools", "arguments": {}}}
```

To create a session:

```json
{"type": "tool_call", "content": {"name": "create_session", "arguments": {"session_id": "my_session"}}}
```

To get a QR code for authentication:

```json
{"type": "tool_call", "content": {"name": "get_qr_code", "arguments": {"session_id": "my_session"}}}
```

To send a message:

```json
{"type": "tool_call", "content": {"name": "send_message", "arguments": {"chat_id": "1234567890@c.us", "content": {"type": "text", "text": "Hello, world!"}}}}
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