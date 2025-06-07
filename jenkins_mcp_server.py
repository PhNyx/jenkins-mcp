#!/usr/bin/env python3
"""
Jenkins MCP Server using FastMCP
Credentials provided at server startup, job URLs provided with tool calls
"""

import asyncio
import json
import logging
import argparse
import os
from typing import Optional, Annotated

from dotenv import load_dotenv
from pydantic import Field
from mcp.server.fastmcp import FastMCP

# Import Jenkins client from the clean module
from jenkins_client import JenkinsClient, JenkinsConfig

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global Jenkins client (initialized at startup)
jenkins_client: Optional[JenkinsClient] = None


def serve():
    """Main MCP server entry point"""
    global jenkins_client
    
    # Parse command line arguments for Jenkins credentials
    parser = argparse.ArgumentParser(description='Jenkins MCP Server')
    parser.add_argument('--jenkins-url', required=True, help='Jenkins base URL')
    parser.add_argument('--username', required=True, help='Jenkins username')
    parser.add_argument('--token', required=True, help='Jenkins API token')
    
    args = parser.parse_args()
    
    # Create Jenkins configuration and client
    jenkins_config = JenkinsConfig(
        base_url=args.jenkins_url,
        username=args.username,
        token=args.token
    )
    jenkins_client = JenkinsClient(jenkins_config)
    
    logger.info(f"Starting Jenkins MCP Server for {jenkins_config.base_url}")
    
    # Create FastMCP server instance
    mcp = FastMCP(name="jenkins-mcp-server")

    @mcp.tool(
        name="fetch_console_log",
        description="Fetch console log from a Jenkins job build using pre-configured credentials."
    )
    async def fetch_console_log_tool(
        job_url: Annotated[str, Field(description="Full Jenkins job URL or job path")],
        build_number: Annotated[Optional[int], Field(description="Specific build number (optional, defaults to latest)", ge=1)] = None,
        parse_errors: Annotated[bool, Field(description="Extract only error-relevant sections (default: True)")] = True,
    ) -> str:
        """Fetch console log from a Jenkins job build using pre-configured credentials."""
        
        try:
            console_log = await jenkins_client.get_console_log(job_url, build_number, parse_errors)
            log_type = "parsed error sections" if parse_errors else "full log"
            return f"Console log ({log_type}) for job {job_url} (build {build_number or 'latest'}):\n\n{console_log}"
            
        except Exception as e:
            return f"Error fetching console log: {str(e)}"

    @mcp.tool(
        name="get_job_info",
        description="Get basic information about a Jenkins job using pre-configured credentials."
    )
    async def get_job_info_tool(
        job_url: Annotated[str, Field(description="Full Jenkins job URL or job path")],
    ) -> str:
        """Get basic information about a Jenkins job using pre-configured credentials."""
        
        try:
            job_info = await jenkins_client.get_job_info(job_url)
            formatted_info = json.dumps(job_info, indent=2)
            return f"Job information for {job_url}:\n\n{formatted_info}"
            
        except Exception as e:
            return f"Error fetching job info: {str(e)}"

    # Run the MCP server
    mcp.run()


if __name__ == "__main__":
    serve() 