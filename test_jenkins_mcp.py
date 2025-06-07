#!/usr/bin/env python3
"""
Simple test script for Jenkins MCP server without OpenAI dependency
"""

import asyncio
import json
from dotenv import load_dotenv
import os
from mcp.client.stdio import StdioServerParameters, stdio_client

load_dotenv()

async def test_jenkins_mcp():
    """Test the Jenkins MCP server directly"""
    
    # Replace with your actual Jenkins credentials
    jenkins_url = os.getenv('JENKINS_URL')
    jenkins_username = os.getenv('JENKINS_USERNAME')  # Replace with actual username
    jenkins_token = os.getenv('JENKINS_TOKEN')    # Replace with actual token
    
    # Create server parameters
    server_params = StdioServerParameters(
        command="python",
        args=[
            "jenkins_mcp_server.py",
            "--jenkins-url", jenkins_url,
            "--username", jenkins_username,
            "--token", jenkins_token
        ]
    )
    
    try:
        async with stdio_client(server_params) as (read, write):
            # Initialize the client
            await write.initialize()
            
            # List available tools
            tools_result = await write.list_tools()
            print("Available tools:")
            for tool in tools_result.tools:
                print(f"  - {tool.name}: {tool.description}")
            
            # Test get_job_info tool
            print("\nTesting get_job_info tool...")
            job_url = f"{jenkins_url}/job/your-actual-job-name/"  # Replace with real job
            
            job_info_result = await write.call_tool(
                "get_job_info",
                arguments={"job_url": job_url}
            )
            print("Job info result:")
            print(job_info_result.content[0].text)
            
            # Test fetch_console_log tool
            print("\nTesting fetch_console_log tool...")
            console_log_result = await write.call_tool(
                "fetch_console_log", 
                arguments={
                    "job_url": job_url,
                    "parse_errors": True
                }
            )
            print("Console log result:")
            print(console_log_result.content[0].text)
            
    except Exception as e:
        print(f"Error testing MCP server: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Testing Jenkins MCP Server...")
    asyncio.run(test_jenkins_mcp()) 