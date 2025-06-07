#!/usr/bin/env python3
"""
Jenkins MCP Server using Pydantic-ai
Credentials provided at server startup, job URLs provided with tool calls
"""

import asyncio
import json
import logging
import argparse
import os
from typing import Optional, Annotated

from dotenv import load_dotenv
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext

# Import Jenkins client from the clean module
from jenkins_client import JenkinsClient, JenkinsConfig

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ServerContext(BaseModel):
    """Context for the MCP server - contains pre-configured Jenkins client"""
    model_config = {"arbitrary_types_allowed": True}
    jenkins_client: JenkinsClient


def create_jenkins_agent():
    """Create Jenkins agent with OpenAI API key from environment"""
    # Get OpenAI API key from environment
    openai_api_key = os.getenv('OPENAI_API_KEY')
    if not openai_api_key:
        raise ValueError("OPENAI_API_KEY environment variable is required")
    
    # Create agent with API key
    return Agent(
        'openai:gpt-4.1',
        deps_type=ServerContext,
        api_key=openai_api_key,
        system_prompt="""You are a Jenkins assistant that helps fetch console logs and job information.
        You have pre-configured Jenkins credentials and can access Jenkins APIs directly."""
    )


# Create Jenkins agent for MCP server (will be initialized with API key from env)
jenkins_mcp_agent = None


async def fetch_console_log(
    ctx: RunContext[ServerContext],
    job_url: Annotated[str, Field(description="Full Jenkins job URL or job path")],
    build_number: Annotated[Optional[int], Field(description="Specific build number (optional, defaults to latest)", ge=1)] = None,
    parse_errors: Annotated[bool, Field(description="Extract only error-relevant sections (default: True)")] = True,
) -> str:
    """Fetch console log from a Jenkins job build using pre-configured credentials."""
    
    try:
        # Use the pre-configured Jenkins client from context
        console_log = await ctx.deps.jenkins_client.get_console_log(job_url, build_number, parse_errors)
        log_type = "parsed error sections" if parse_errors else "full log"
        return f"Console log ({log_type}) for job {job_url} (build {build_number or 'latest'}):\n\n{console_log}"
        
    except Exception as e:
        return f"Error fetching console log: {str(e)}"


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
    
    # Initialize the Jenkins agent with environment variables
    global jenkins_mcp_agent
    try:
        jenkins_mcp_agent = create_jenkins_agent()
        
        # Register tools with the initialized agent
        jenkins_mcp_agent.tool(fetch_console_log)
        jenkins_mcp_agent.tool(get_job_info)
        
    except ValueError as e:
        logger.error(f"Failed to initialize Jenkins agent: {e}")
        logger.error("Please ensure OPENAI_API_KEY is set in your .env file or environment")
        return
    
    parser = argparse.ArgumentParser(description='Jenkins MCP Server')
    parser.add_argument('--jenkins-url', required=True, help='Jenkins base URL')
    parser.add_argument('--username', required=True, help='Jenkins username')
    parser.add_argument('--token', required=True, help='Jenkins API token')
    parser.add_argument('--analyze-job', help='Specific job URL to analyze (optional)')
    parser.add_argument('--interactive', action='store_true', help='Run in interactive mode for testing')
    
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
    logger.info(f"OpenAI API key loaded: {'Yes' if os.getenv('OPENAI_API_KEY') else 'No'}")
    
    # Handle different modes
    if args.analyze_job:
        # Analyze a specific job URL
        logger.info(f"Analyzing job: {args.analyze_job}")
        result = await jenkins_mcp_agent.run(
            f"Please analyze the Jenkins build at {args.analyze_job}. Get the job information and console log to help me understand what happened.",
            deps=server_context
        )
        print("\n" + "="*80)
        print("JENKINS BUILD ANALYSIS")
        print("="*80)
        print(result.output)
        print("="*80)
        
    elif args.interactive:
        # Interactive mode for testing
        print("\n" + "="*60)
        print("JENKINS MCP SERVER - INTERACTIVE MODE")
        print("="*60)
        print("Enter Jenkins job URLs to analyze, or 'quit' to exit.")
        print("Example: https://jenkins.company.com/job/my-project/123/")
        print("-"*60)
        
        while True:
            try:
                job_url = input("\nEnter job URL (or 'quit'): ").strip()
                if job_url.lower() in ['quit', 'exit', 'q']:
                    break
                    
                if not job_url:
                    continue
                    
                print(f"\nAnalyzing: {job_url}")
                print("-" * 40)
                
                result = await jenkins_mcp_agent.run(
                    f"Please analyze the Jenkins build at {job_url}. Get the job information and console log to help me understand what happened.",
                    deps=server_context
                )
                
                print(result.output)
                print("-" * 40)
                
            except KeyboardInterrupt:
                print("\nExiting...")
                break
            except Exception as e:
                print(f"Error: {e}")
    
    else:
        # This is where you would integrate with actual MCP server protocol
        # For now, just show available tools
        print("\n" + "="*60)
        print("JENKINS MCP SERVER - READY")
        print("="*60)
        print("The server is ready to accept MCP requests.")
        print("Available tools:")
        print("  - fetch_console_log: Get console logs from Jenkins builds")
        print("  - get_job_info: Get job/build information")
        print("")
        print("To test the server:")
        print(f"  python {__file__} --jenkins-url {args.jenkins_url} --username {args.username} --token YOUR_TOKEN --interactive")
        print(f"  python {__file__} --jenkins-url {args.jenkins_url} --username {args.username} --token YOUR_TOKEN --analyze-job JOB_URL")
        print("="*60)


if __name__ == "__main__":
    asyncio.run(main()) 