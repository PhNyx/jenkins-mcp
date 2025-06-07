#!/usr/bin/env python3
"""
Simple test for Jenkins MCP server using the same pattern as the client example
"""

import asyncio
import os
import argparse
from dotenv import load_dotenv
from pydantic_ai.mcp import MCPServerStdio
from jenkins_client import JenkinsClient, JenkinsConfig

load_dotenv()

async def test_jenkins_mcp(full_url, override_build_number=None):
    """Test the Jenkins MCP server connection and tools"""
    
    # Get Jenkins credentials from environment variables
    jenkins_url = os.getenv('JENKINS_URL')
    jenkins_username = os.getenv('JENKINS_USERNAME')
    jenkins_token = os.getenv('JENKINS_TOKEN')
    
    if not all([jenkins_url, jenkins_username, jenkins_token]):
        print("Error: Please set JENKINS_URL, JENKINS_USERNAME, and JENKINS_TOKEN environment variables")
        return
    
    # Create a temporary Jenkins client to use its URL parsing functionality
    temp_config = JenkinsConfig(
        base_url=jenkins_url,
        username=jenkins_username,
        token=jenkins_token
    )
    temp_client = JenkinsClient(temp_config)
    
    # Parse the full URL to extract job path and build number using Jenkins client
    try:
        job_path, build_number = temp_client._extract_job_path(full_url)
        # Convert job path back to full URL format for the MCP server
        job_url = f"{jenkins_url}/{job_path}/"
    except Exception as e:
        print(f"Error parsing Jenkins URL: {e}")
        return
    
    # Override build number if specified
    if override_build_number is not None:
        build_number = override_build_number
    
    print(f"Parsed job URL: {job_url}")
    if build_number:
        print(f"Build number: {build_number}")
    
    print("Creating MCP server connection...")
    
    # Create MCP server connection (this will spawn the server subprocess)
    jenkins_server = MCPServerStdio(
        command="python",
        args=[
            "jenkins_mcp_server.py",
            "--jenkins-url", jenkins_url,
            "--username", jenkins_username, 
            "--token", jenkins_token
        ],
        tool_prefix="jenkins",
        timeout=10.0
    )
    
    try:
        print("Starting MCP server...")
        async with jenkins_server:
            print("Connected to Jenkins MCP server!")
            
            # List available tools
            tools = await jenkins_server.list_tools()
            print("Available tools:")
            for tool in tools:
                print(f"  - {tool.name}: {tool.description}")
            
            # Test the get_job_info tool
            print(f"\nTesting get_job_info tool with job: {job_url}")
            
            try:
                result = await jenkins_server.call_tool(
                    "jenkins_get_job_info",  # Note: prefixed with "jenkins_"
                    {"job_url": job_url}
                )
                print("Job info result:")
                print(result)
            except Exception as e:
                print(f"Error calling get_job_info: {e}")
            
            # Test the fetch_console_log tool
            print(f"\nTesting fetch_console_log tool..." + (f" (build #{build_number})" if build_number else " (latest build)"))
            try:
                console_log_args = {
                    "job_url": job_url,
                    "parse_errors": True
                }
                if build_number:
                    console_log_args["build_number"] = build_number
                    
                result = await jenkins_server.call_tool(
                    "jenkins_fetch_console_log",  # Note: prefixed with "jenkins_"
                    console_log_args
                )
                print("Console log result:")
                print(result)
            except Exception as e:
                print(f"Error calling fetch_console_log: {e}")
                
    except Exception as e:
        print(f"Error connecting to MCP server: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Test Jenkins MCP Server')
    parser.add_argument('full_url', help='Full Jenkins URL including build number (e.g., https://jenkins.example.com/job/my-project/123)')
    parser.add_argument('--build-number', type=int, help='Override build number (optional, overrides build number from URL)')
    
    args = parser.parse_args()
    
    print("Testing Jenkins MCP Server Connection...")
    print(f"Full URL: {args.full_url}")
    if args.build_number:
        print(f"Override Build Number: {args.build_number}")
    
    asyncio.run(test_jenkins_mcp(args.full_url, args.build_number)) 