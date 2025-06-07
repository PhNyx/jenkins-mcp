#!/usr/bin/env python3
"""
Test script for Jenkins MCP Server with AI Agent
Tests the full MCP server functionality including AI agent interactions
"""

import asyncio
import os
import json
from dotenv import load_dotenv

load_dotenv()

# Import the Jenkins client and MCP server components
from jenkins_client import JenkinsClient, JenkinsConfig
from jenkins_mcp_server import create_jenkins_agent, ServerContext, fetch_console_log, get_job_info

async def test_mcp_server():
    """Test the Jenkins MCP Server with AI agent functionality"""
    
    print("Jenkins MCP Server Test")
    print("=" * 50)
    
    # Check prerequisites
    print("Checking prerequisites:")
    print("-" * 30)
    
    # Check for OpenAI API key
    openai_key = os.getenv('OPENAI_API_KEY')
    if openai_key:
        print(f"  ✓ OpenAI API Key: {'*' * 20}{openai_key[-4:]}")
        test_ai_agent = True
    else:
        print("  ✗ OpenAI API Key: NOT FOUND")
        print("  Will test Jenkins client only (without AI agent)")
        test_ai_agent = False
    
    # Check for Jenkins credentials
    jenkins_url = os.getenv('JENKINS_URL')
    jenkins_username = os.getenv('JENKINS_USERNAME')
    jenkins_token = os.getenv('JENKINS_TOKEN')
    
    if jenkins_url and jenkins_username and jenkins_token:
        print(f"  ✓ Jenkins URL: {jenkins_url}")
        print(f"  ✓ Jenkins Username: {jenkins_username}")
        print(f"  ✓ Jenkins Token: {'*' * 20}{jenkins_token[-4:]}")
    else:
        print("  ✗ Jenkins credentials incomplete")
        print("  Please set JENKINS_URL, JENKINS_USERNAME, and JENKINS_TOKEN")
        return
    
    print("\nInitializing Jenkins MCP Server...")
    print("-" * 30)
    
    try:
        # Create Jenkins configuration
        jenkins_config = JenkinsConfig(
            base_url=jenkins_url,
            username=jenkins_username,
            token=jenkins_token
        )
        
        # Create Jenkins client
        jenkins_client = JenkinsClient(jenkins_config)
        
        # Create server context
        server_context = ServerContext(jenkins_client=jenkins_client)
        
        # Create Jenkins agent only if OpenAI API key is available
        jenkins_agent = None
        if test_ai_agent:
            jenkins_agent = create_jenkins_agent()
            
            # Register tools with the agent
            jenkins_agent.tool(fetch_console_log)
            jenkins_agent.tool(get_job_info)
            
            print("  ✓ Jenkins MCP Server with AI agent initialized successfully!")
        else:
            print("  ✓ Jenkins client initialized successfully!")
        
    except Exception as e:
        print(f"  ✗ Failed to initialize MCP server: {e}")
        return
    
    # Test job URL for your environment
    test_job_url = "https://core.jenkins.hyperloop.sonynei.net/monetization-core/job/subscriptions-serverless/job/unified-ci-onboarding/16/"
    
    if test_ai_agent and jenkins_agent:
        print("\nTesting AI Agent with Natural Language Queries...")
        print("-" * 30)
        
        # Test queries
        test_queries = [
            f"Get information about the Jenkins job at {test_job_url}",
            f"Fetch the console log for the Jenkins build at {test_job_url}",
            "What can you tell me about this Jenkins build?",
        ]
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n{i}. Testing query: '{query}'")
            print("   " + "-" * 50)
            
            try:
                result = await jenkins_agent.run(query, deps=server_context)
                print(f"   ✓ Response received:")
                print(f"   {result.data}")
                
            except Exception as e:
                print(f"   ✗ Query failed: {e}")
            
            print()
    else:
        print("\nSkipping AI Agent tests (no OpenAI API key)")
        print("-" * 30)
    
    print("\nTesting Direct Tool Calls...")
    print("-" * 30)
    
    # Test direct tool calls (without AI agent)
    try:
        # Create a mock context for direct tool testing
        class MockContext:
            def __init__(self, server_context):
                self.deps = server_context
        
        mock_ctx = MockContext(server_context)
        
        print("1. Testing get_job_info tool directly:")
        job_info_result = await get_job_info(mock_ctx, test_job_url)
        print(f"   ✓ Job info retrieved successfully")
        print(f"   Response length: {len(job_info_result)} characters")
        
        print("\n2. Testing fetch_console_log tool directly (parsed):")
        console_log_result = await fetch_console_log(mock_ctx, test_job_url, None, True)
        print(f"   ✓ Parsed console log retrieved successfully")
        print(f"   Response length: {len(console_log_result)} characters")
        
        print("\n3. Testing fetch_console_log tool directly (full log):")
        console_log_full_result = await fetch_console_log(mock_ctx, test_job_url, None, False)
        print(f"   ✓ Full console log retrieved successfully")
        print(f"   Response length: {len(console_log_full_result)} characters")
        
    except Exception as e:
        print(f"   ✗ Direct tool test failed: {e}")
    
    print("\n" + "=" * 50)
    print("MCP Server Test Complete!")
    
    if test_ai_agent:
        print("\nIf all tests passed, your Jenkins MCP Server is working correctly!")
        print("You can now use it with MCP-compatible clients like Claude Desktop.")
        print("\nTo run the MCP server:")
        print(f"python jenkins_mcp_server.py --jenkins-url {jenkins_url} --username {jenkins_username} --token YOUR_TOKEN")
    else:
        print("\nJenkins client tests completed successfully!")
        print("To test the full MCP server with AI agent, set OPENAI_API_KEY in your .env file.")
        print("The AI agent enables natural language queries about Jenkins jobs.")


if __name__ == "__main__":
    asyncio.run(test_mcp_server()) 