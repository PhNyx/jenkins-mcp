#!/usr/bin/env python3
"""
Simple test script for Jenkins MCP Server
Run this to test basic functionality without a full MCP client
"""

import asyncio
import json
from jenkins_agent import JenkinsClient, JenkinsConfig


async def test_jenkins_client():
    """Test the Jenkins client functionality"""
    
    # Example configuration - replace with your actual Jenkins details
    config = JenkinsConfig(
        base_url="https://your-jenkins-instance.com",
        username="your-username",
        token="your-api-token"
    )
    
    client = JenkinsClient(config)
    
    try:
        # Test URL parsing
        test_urls = [
            "https://jenkins.company.com/job/my-project/job/main/",
            "my-project/main",
            "https://jenkins.company.com/job/folder/job/subfolder/job/project/"
        ]
        
        print("Testing URL parsing:")
        for url in test_urls:
            try:
                job_path = client._extract_job_path(url)
                print(f"  {url} -> {job_path}")
            except Exception as e:
                print(f"  {url} -> ERROR: {e}")
        
        print("\nTo test actual Jenkins connectivity, update the config above with your Jenkins details.")
        print("Then uncomment the following lines:")
        
        # Uncomment these lines and update the job_url to test actual Jenkins API calls
        # job_url = "your-job-url-here"
        # 
        # print(f"\nTesting job info for: {job_url}")
        # job_info = await client.get_job_info(job_url)
        # print(json.dumps(job_info, indent=2))
        # 
        # print(f"\nTesting console log for: {job_url}")
        # console_log = await client.get_console_log(job_url)
        # print(f"Console log length: {len(console_log)} characters")
        # print("First 500 characters:")
        # print(console_log[:500])
        
    except Exception as e:
        print(f"Test failed: {e}")


if __name__ == "__main__":
    print("Jenkins MCP Server Test")
    print("=" * 50)
    asyncio.run(test_jenkins_client()) 