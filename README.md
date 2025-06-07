# Jenkins MCP Server with FastMCP

A Jenkins integration using FastMCP that provides console log fetching capabilities via MCP (Model Context Protocol) server. 

**Key Design**: Jenkins credentials are provided once when the MCP server starts, and tool calls only need job URLs.

## Features

- **Fetch Jenkins Console Logs**: Retrieve console output from Jenkins job builds
- **Job Information**: Get basic information about Jenkins jobs
- **Flexible URL Handling**: Supports both full Jenkins URLs and job paths
- **Latest Build Support**: Automatically fetches the latest build if no build number is specified
- **Secure Credential Handling**: Jenkins credentials provided at server startup, not with each tool call
- **True MCP Server**: Uses FastMCP to implement a proper MCP server that other agents can connect to

## Architecture

This implementation uses the Model Context Protocol (MCP) architecture:

1. **MCP Server** (`jenkins_mcp_server.py`): Runs as a subprocess and exposes Jenkins tools via MCP protocol
2. **MCP Client**: Other Pydantic AI agents connect to the server using `MCPServerStdio`

```
┌─────────────────┐    MCPServerStdio    ┌─────────────────┐
│   Main Agent    │ ◄─────────────────► │ Jenkins MCP     │
│                 │      (subprocess)    │ Server          │
│ (with OpenAI)   │                      │ (FastMCP)       │
└─────────────────┘                      └─────────────────┘
                                                  │
                                                  ▼
                                         ┌─────────────────┐
                                         │ Jenkins API     │
                                         │                 │
                                         └─────────────────┘
```

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Jenkins API Token

To use this server, you'll need a Jenkins API token:

1. Log into your Jenkins instance
2. Go to your user profile (click your name in the top-right corner)
3. Click "Configure" 
4. In the "API Token" section, click "Add new Token"
5. Give it a name and click "Generate"
6. Copy the generated token (you won't be able to see it again)

### 3. OpenAI API Key

Set your OpenAI API key in your environment or `.env` file:

```bash
export OPENAI_API_KEY="your-api-key-here"
```

## Usage

### Method 1: Use via Pydantic AI MCPServerStdio (Recommended)

This is the proper MCP way - the Jenkins server runs as a subprocess and other agents connect to it:

```python
from pydantic_ai.mcp import MCPServerStdio
from pydantic_ai import Agent

# Create MCP server with credentials at startup
jenkins_server = MCPServerStdio(
    command="python",
    args=[
        "jenkins_mcp_server.py",
        "--jenkins-url", "https://your-jenkins.com",
        "--username", "your-username", 
        "--token", "your-api-token"
    ],
    tool_prefix="jenkins"
)

# Use in another agent
main_agent = Agent('openai:gpt-4o-mini', mcp_servers=[jenkins_server])

async with main_agent.run_mcp_servers():
    result = await main_agent.run(
        "Please fetch the console log for job https://jenkins.company.com/job/my-project/"
    )
    print(result.data)
```

### Method 2: Direct MCP Server Testing

For testing the MCP server directly:

```bash
python jenkins_mcp_server.py \
  --jenkins-url https://your-jenkins.com \
  --username your-username \
  --token your-api-token
```

This will start the MCP server and wait for MCP client connections via stdin/stdout.

## Example Client

See `jenkins_mcp_client_example.py` for a complete example of how to use the Jenkins MCP server from another Pydantic AI agent.

## Available MCP Tools

When connected via MCPServerStdio, the following tools are available (with `jenkins_` prefix by default):

- `jenkins_fetch_console_log`: Get console logs from Jenkins builds
- `jenkins_get_job_info`: Get job/build information

## Development

### Project Structure

```
├── jenkins_mcp_server.py          # Main MCP server (FastMCP)
├── jenkins_mcp_client_example.py  # Example client usage
├── jenkins_client.py              # Jenkins API client
├── test_mcp_server.py             # Tests
└── requirements.txt               # Dependencies
```

### Testing

Run the test suite:

```bash
python test_mcp_server.py
```

## MCP Protocol Benefits

Using the MCP protocol provides several advantages:

1. **Standardization**: Works with any MCP-compatible client (Claude Desktop, other AI frameworks)
2. **Security**: Credentials are isolated in the server process
3. **Reusability**: Multiple agents can connect to the same server
4. **Tool Namespacing**: Tool prefixes prevent naming conflicts
5. **Process Isolation**: Server runs in separate process for better stability

## Troubleshooting

### Common Issues

1. **MCP Dependencies**: Make sure you have `mcp>=1.9.2` installed
2. **FastMCP Import Error**: Ensure all dependencies are properly installed
3. **Jenkins Authentication**: Verify your API token has the necessary permissions
4. **OpenAI API Key**: Required for the client agent (not the MCP server itself)

### Debug Mode

Add logging to see MCP communication:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License 