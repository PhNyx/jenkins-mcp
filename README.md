# Jenkins MCP Server with Pydantic-ai

A Jenkins integration using Pydantic-ai that provides console log fetching capabilities via MCP (Model Context Protocol) server. 

**Key Design**: Jenkins credentials are provided once when the MCP server starts, and tool calls only need job URLs.

## Features

- **Fetch Jenkins Console Logs**: Retrieve console output from Jenkins job builds
- **Job Information**: Get basic information about Jenkins jobs
- **Flexible URL Handling**: Supports both full Jenkins URLs and job paths
- **Latest Build Support**: Automatically fetches the latest build if no build number is specified
- **Secure Credential Handling**: Jenkins credentials provided at server startup, not with each tool call
- **Pydantic-ai Integration**: Uses Pydantic-ai's built-in MCP server capabilities

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

## Usage

### 1. Start MCP Server with Credentials

```bash
python jenkins_mcp_server.py \
  --jenkins-url https://your-jenkins.com \
  --username your-username \
  --token your-api-token
```

### 2. Use via Pydantic-ai MCPServerStdio

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

# Tool calls only need job URLs
async with main_agent.run_mcp_servers():
    result = await main_agent.run(
        "Get console log for https://jenkins.com/job/my-project/"
    )
```

### 3. Direct Agent Usage (for testing)

```bash
python jenkins_agent.py
```

### Available Tools

#### 1. `fetch_console_log`

Fetches the console log from a Jenkins job build using pre-configured credentials.

**Parameters:**
- `job_url` (required): Full Jenkins job URL or job path
- `build_number` (optional): Specific build number (defaults to latest build)

**Example job URLs:**
- Full URL: `https://jenkins.company.com/job/my-project/job/main/`
- Job path: `my-project/main`

#### 2. `get_job_info`

Gets basic information about a Jenkins job using pre-configured credentials.

**Parameters:**
- `job_url` (required): Full Jenkins job URL or job path

### Supported Jenkins URL Formats

The server can handle various Jenkins URL formats:

- Standard jobs: `/job/jobname/`
- Folder-based jobs: `/job/folder/job/jobname/`
- Multi-level folders: `/job/folder1/job/folder2/job/jobname/`
- Direct job paths: `folder/jobname`

### Example Usage with MCP Client

When integrated with an MCP client, tool calls only need job URLs:

```json
{
  "method": "tools/call",
  "params": {
    "name": "jenkins_fetch_console_log",
    "arguments": {
      "job_url": "https://jenkins.company.com/job/my-project/job/main/",
      "build_number": 42
    }
  }
}
```

Note: Tool names are prefixed with `jenkins_` when using the `tool_prefix="jenkins"` setting.

## Security Considerations

- **Never commit API tokens to version control**
- Credentials are provided only at server startup, not with each tool call
- No credential storage or caching in the server
- Uses HTTPS when possible for Jenkins communication
- API tokens should be scoped appropriately in Jenkins
- Credentials are isolated within the MCP server subprocess

## Error Handling

The server provides detailed error messages for common issues:

- Invalid Jenkins URLs
- Authentication failures
- Network connectivity issues
- Missing builds or jobs
- Permission denied errors

## Development

### Project Structure

```
├── jenkins_agent.py           # Jenkins agent (for direct use, expects credentials per call)
├── jenkins_mcp_server.py      # MCP server (credentials at startup, job URLs in calls)
├── jenkins_mcp_example.py     # Example usage with MCP integration
├── test_server.py             # Testing utilities
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

### Key Components

- **jenkins_agent.py**: Direct-use agent (credentials per call)
- **jenkins_mcp_server.py**: MCP server (credentials at startup)
- **JenkinsClient**: Handles Jenkins API interactions
- **JenkinsConfig**: Pydantic model for Jenkins connection configuration  
- **MCPServerStdio**: Pydantic-ai's built-in MCP server integration

### Adding New Features

To add new Jenkins-related tools:

1. Add methods to the `JenkinsClient` class in `jenkins_agent.py`
2. Add new tool functions to `jenkins_mcp_server.py` decorated with `@jenkins_mcp_agent.tool`
3. Follow the pattern: credentials from context, job URLs as parameters
4. Use Pydantic-ai's tool function signature patterns with `RunContext[ServerContext]`

## Troubleshooting

### Common Issues

1. **Authentication Error**: Verify your username and API token
2. **Job Not Found**: Check the job URL format and permissions
3. **Network Timeout**: Increase timeout values for slow Jenkins instances
4. **SSL Certificate Issues**: Jenkins server may have self-signed certificates

### Debug Mode

Set logging level to DEBUG for more detailed output:

```python
logging.basicConfig(level=logging.DEBUG)
```

## License

This project is open source. Please check with your organization's policies before using with internal Jenkins instances. 