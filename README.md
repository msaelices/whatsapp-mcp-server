# WhatsApp MCP Server

A server that provides a Model Context Protocol (MCP) interface to interact with WhatsApp Business API using FastMCP.

## Introduction

WhatsApp MCP Server is a Python implementation that enables language models like Claude to interact with WhatsApp functionality through [GreenAPI](https://green-api.com/). It leverages FastMCP for improved performance, better developer experience, and a cleaner implementation.

## Features

- **Messaging**: Send text messages to WhatsApp contacts
- **Group Management**: Create groups, list members, add/remove participants
- **Session Handling**: Manage WhatsApp API sessions
- **Chat History**: Retrieve chat lists and message history

## WhatsApp API Client

This project uses the `whatsapp-api-client-python` library to interact with WhatsApp. The client provides access to the WhatsApp Cloud API, which requires a [GreenAPI](https://green-api.com/) account to use.

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
# Run the MCP server on default host (127.0.0.1) and port (8000)
whatsapp-mcp

# Specify host and port
whatsapp-mcp --host 0.0.0.0 --port 9000
```

For debugging:

```bash
whatsapp-mcp --debug
```

The server communicates using the Model Context Protocol (MCP) and can be accessed via HTTP or WebSockets when running with FastMCP.

### Available Tools

- `open_session`: Open a new WhatsApp session
- `send_message`: Send a message to a chat
- `get_chats`: Get a list of chats
- `create_group`: Create a new WhatsApp group
- `get_group_participants`: Get the participants of a group

## FastMCP API Reference

The WhatsApp MCP Server uses FastMCP to provide both WebSocket and HTTP endpoints:

- WebSocket: `ws://localhost:8000/mcp`
- HTTP: `http://localhost:8000/mcp`

You can test the API directly using tools like curl:

```bash
# List available tools
curl -X POST http://localhost:8000/mcp/listTools

# Call a tool
curl -X POST http://localhost:8000/mcp/callTool \
  -H "Content-Type: application/json" \
  -d '{"name": "open_session", "arguments": {}}'
```

## How to add it to Claude Code

To add a WhatsApp server to Claude, use the `claude mcp add` command:

```bash
# Add the WhatsApp MCP server
$ claude mcp add whatsapp -- whatsapp-mcp

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

## Using with Claude Desktop

To use the WhatsApp MCP server with Claude Desktop, you need to add it to your `claude_desktop_config.json` file:

### Using pip installation (recommended)

```json
"mcpServers": {
  "whatsapp": {
    "command": "python",
    "args": ["-m", "whatsapp_mcp"]
  }
}
```

### Using the executable

```json
"mcpServers": {
  "whatsapp": {
    "command": "whatsapp-mcp"
  }
}
```

### Using Docker

```json
"mcpServers": {
  "whatsapp": {
    "command": "docker",
    "args": ["run", "--rm", "-i", "-e", "GREENAPI_ID_INSTANCE=your_instance_id", "-e", "GREENAPI_API_TOKEN=your_api_token", "whatsapp-mcp-server"]
  }
}
```

Remember to set your GreenAPI credentials either as environment variables or in your `.env` file before starting Claude Desktop.

### Command-line options

The WhatsApp MCP server accepts these command-line arguments:
- `--debug`: Increase verbosity level for debugging
- `--host`: Host to bind the server to (default: 127.0.0.1)
- `--port`: Port to bind the server to (default: 8000)

### Debugging

For debugging the MCP server:
- Use MCP inspector: `npx @modelcontextprotocol/inspector whatsapp-mcp`
- View logs in your Claude Desktop logs directory (typically `~/Library/Logs/Claude/` on macOS)
- Access the FastMCP web interface at http://localhost:8000 for interactive API documentation

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

The project uses a modern `pyproject.toml` configuration which includes:
- Core dependencies needed for running the application
- Development dependencies available with `pip install -e ".[dev]"`

## License

This project is licensed under the MIT License - see the LICENSE file for details.