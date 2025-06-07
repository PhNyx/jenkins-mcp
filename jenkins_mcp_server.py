#!/usr/bin/env python3
"""
Jenkins MCP Server using Pydantic-ai
Credentials provided at server startup, job URLs provided with tool calls
"""

import asyncio
import json
import logging
import argparse
from typing import Optional, Annotated

from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext

# Import Jenkins client from the other module
from jenkins_agent import JenkinsClient, JenkinsConfig

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ServerContext(BaseModel):
    """Context for the MCP server - contains pre-configured Jenkins client"""
    jenkins_client: JenkinsClient


# Create Jenkins agent for MCP server (credentials come from context)
jenkins_mcp_agent = Agent(
    'openai:gpt-4o-mini',
    deps_type=ServerContext,
    system_prompt="""You are a Jenkins assistant that helps fetch console logs and job information.
    You have pre-configured Jenkins credentials and can access Jenkins APIs directly."""
)


@jenkins_mcp_agent.tool
async def fetch_console_log(
    ctx: RunContext[ServerContext],
    job_url: Annotated[str, Field(description="Full Jenkins job URL or job path")],
    build_number: Annotated[Optional[int], Field(description="Specific build number (optional, defaults to latest)", ge=1)] = None,
) -> str:
    """Fetch console log from a Jenkins job build using pre-configured credentials."""
    
    try:
        # Use the pre-configured Jenkins client from context
        console_log = await ctx.deps.jenkins_client.get_console_log(job_url, build_number)
        return f"Console log for job {job_url} (build {build_number or 'latest'}):\n\n{console_log}"
        
    except Exception as e:
        return f"Error fetching console log: {str(e)}"


@jenkins_mcp_agent.tool  
async def get_job_info(
    ctx: RunContext[ServerContext],
    job_url: Annotated[str, Field(description="Full Jenkins job URL or job path")],
) -> str:
    """Get basic information about a Jenkins job using pre-configured credentials."""
    
    try:
        # Use the pre-configured Jenkins client from context
        job_info = await ctx.deps.jenkins_client.get_job_info(job_url)
        formatted_info = json.dumps(job_info, indent=2)
        return f"Job information for {job_url}:\n\n{formatted_info}"
        
    except Exception as e:
        return f"Error fetching job info: {str(e)}"


async def main():
    """Main entry point for MCP server - reads credentials from command line"""
    
    parser = argparse.ArgumentParser(description='Jenkins MCP Server')
    parser.add_argument('--jenkins-url', required=True, help='Jenkins base URL')
    parser.add_argument('--username', required=True, help='Jenkins username')
    parser.add_argument('--token', required=True, help='Jenkins API token')
    
    args = parser.parse_args()
    
    # Create Jenkins configuration from command line arguments
    jenkins_config = JenkinsConfig(
        base_url=args.jenkins_url,
        username=args.username,
        token=args.token
    )
    
    # Create Jenkins client 
    jenkins_client = JenkinsClient(jenkins_config)
    
    # Create server context with pre-configured client
    server_context = ServerContext(jenkins_client=jenkins_client)
    
    logger.info(f"Starting Jenkins MCP Server for {jenkins_config.base_url}")
    
    # This is where you would integrate with actual MCP server protocol
    # For now, this demonstrates how the tools work with pre-configured credentials
    
    # Example usage (remove in actual MCP server)
    result = await jenkins_mcp_agent.run(
        "Please help me with Jenkins job information",
        deps=server_context
    )
    
    print(result.data)


if __name__ == "__main__":
    asyncio.run(main()) 