#!/usr/bin/env python3
"""
Example showing correct usage of Jenkins MCP server with Pydantic-ai
Credentials provided at server startup, job URLs provided with tool calls
"""

import asyncio
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStdio


async def run_with_mcp_server():
    """Example using Jenkins MCP server with credentials provided at startup"""
    
    # Create MCP server with Jenkins credentials provided as command arguments
    jenkins_server = MCPServerStdio(
        command="python",
        args=[
            "jenkins_mcp_server.py",
            "--jenkins-url", "https://your-jenkins.com",
            "--username", "your-username", 
            "--token", "your-api-token"
        ],
        tool_prefix="jenkins",
        timeout=10.0
    )
    
    # Create main agent that uses the Jenkins MCP server
    main_agent = Agent(
        'openai:gpt-4o-mini',
        mcp_servers=[jenkins_server],
        system_prompt="""You are a helpful assistant with access to Jenkins via MCP.
        You can fetch console logs and job information. The Jenkins credentials are 
        already configured in the MCP server, so you only need job URLs."""
    )
    
    # Now the client just needs to provide the job URL, not credentials
    async with main_agent.run_mcp_servers():
        result = await main_agent.run(
            "Please fetch the console log for job https://jenkins.company.com/job/my-project/job/main/"
        )
        print("Agent response:", result.data)


async def run_with_environment_variables():
    """Alternative: Use environment variables for credentials"""
    
    jenkins_server = MCPServerStdio(
        command="python",
        args=["jenkins_mcp_server.py"],
        env={
            "JENKINS_URL": "https://your-jenkins.com",
            "JENKINS_USERNAME": "your-username",
            "JENKINS_TOKEN": "your-api-token"
        },
        tool_prefix="jenkins"
    )
    
    main_agent = Agent('openai:gpt-4o-mini', mcp_servers=[jenkins_server])
    
    async with main_agent.run_mcp_servers():
        result = await main_agent.run(
            "Get the latest console log for job my-project/main"
        )
        print(result.data)


async def main():
    """Main example runner"""
    print("Jenkins MCP Server Example")
    print("=" * 50)
    print("This shows how to use Jenkins MCP server where:")
    print("- Server startup: Provides Jenkins credentials")
    print("- Tool calls: Only need job URLs")
    print()
    
    # In practice, you'd run this
    # asyncio.run(run_with_mcp_server())
    
    print("To actually run this:")
    print("1. Start the MCP server with your Jenkins credentials")
    print("2. The server tools will only ask for job URLs")
    print("3. Credentials are handled internally by the server")


if __name__ == "__main__":
    asyncio.run(main()) 