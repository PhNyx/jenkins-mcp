#!/usr/bin/env python3
"""
Example client that connects to the Jenkins MCP server using MCPServerStdio
This demonstrates how to use the Jenkins MCP server as a subprocess
"""

import asyncio
import os
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStdio


async def main():
    """Example using Jenkins MCP server with credentials provided at startup"""
    
    # Replace these with your actual Jenkins credentials
    jenkins_url = "https://your-jenkins.com"
    jenkins_username = "your-username"
    jenkins_token = "your-api-token"
    
    # Create MCP server with Jenkins credentials provided as command arguments
    jenkins_server = MCPServerStdio(
        command="python",
        args=[
            "jenkins_mcp_server.py",
            "--jenkins-url", jenkins_url,
            "--username", jenkins_username, 
            "--token", jenkins_token
        ],
        tool_prefix="jenkins",  # Prefix tools to avoid conflicts
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
    
    # Example usage
    async with main_agent.run_mcp_servers():
        print("Connected to Jenkins MCP server!")
        
        # Example 1: Get job information
        result = await main_agent.run(
            "Please get information about the job at https://jenkins.company.com/job/my-project/"
        )
        print("Job Info Result:", result.data)
        
        # Example 2: Get console log
        result = await main_agent.run(
            "Please fetch the console log for the latest build of https://jenkins.company.com/job/my-project/"
        )
        print("Console Log Result:", result.data)
        
        # Example 3: Analyze a specific build
        result = await main_agent.run(
            "Please analyze build #123 of https://jenkins.company.com/job/my-project/ - get both job info and console log to help me understand what happened"
        )
        print("Analysis Result:", result.data)


if __name__ == "__main__":
    # Make sure OpenAI API key is set
    if not os.getenv('OPENAI_API_KEY'):
        print("Please set your OPENAI_API_KEY environment variable")
        exit(1)
    
    asyncio.run(main()) 