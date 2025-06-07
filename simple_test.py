#!/usr/bin/env python3
"""
Simple test for Jenkins MCP Server - tests only the JenkinsClient
without requiring OpenAI API keys or full Agent setup
"""

import asyncio
import sys
import os
from dotenv import load_dotenv

load_dotenv()

# Add current directory to path so we can import the modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import only what we need for testing
from jenkins_agent import JenkinsClient, JenkinsConfig


async def test_jenkins_client():
    """Test the Jenkins client functionality"""
    
    print("Jenkins MCP Server - Simple Test")
    print("=" * 50)
    
    # Example configuration - replace with your actual Jenkins details
    config = JenkinsConfig(
        base_url=os.getenv('JENKINS_URL'),
        username=os.getenv('JENKINS_USERNAME'),
        token=os.getenv('JENKINS_TOKEN')
    )
    
    client = JenkinsClient(config)
    
    print("Testing URL parsing functionality:")
    print("-" * 30)
    
    # Test URL parsing
    test_urls = [
        "https://core.jenkins.hyperloop.sonynei.net/shared-tools/job/workflow-pipelines/job/onboarding/job/unified-jenkins-log-parser-agent/14/consoleText",
        "https://core.jenkins.hyperloop.sonynei.net/shared-tools/job/workflow-pipelines/job/onboarding/job/unified-ci-migration-agent/106/",
        "https://core.jenkins.hyperloop.sonynei.net/monetization-core/job/subscriptions-serverless/job/unified-ci-onboarding/16/"
    ]
    
    for url in test_urls:
        try:
            job_path, build_number = client._extract_job_path(url)
            print(f"  ✓ {url}")
            print(f"    -> Job Path: {job_path}")
            if build_number:
                print(f"    -> Build Number: {build_number}")
        except Exception as e:
            print(f"  ✗ {url}")
            print(f"    -> ERROR: {e}")
        print()
    
    print("\nURL parsing test completed!")
    print("\nTo test actual Jenkins connectivity:")
    print("1. Update the config above with your real Jenkins details")  
    print("2. Uncomment the lines below and run again")
    print("\n" + "="*50)
    
    # Uncomment these lines and update the job_url to test actual Jenkins API calls
    # You'll need real Jenkins credentials for this to work
    
    # Use one of the actual job URLs from your Jenkins instance
    job_url = "https://core.jenkins.hyperloop.sonynei.net/monetization-core/job/subscriptions-serverless/job/unified-ci-onboarding/16/"
    
    try:
        print(f"Testing job info for: {job_url}")
        print("(Since URL ends with /106/, this will fetch build #106 info, not general job info)")
        job_info = await client.get_job_info(job_url)
        print("Build info retrieved successfully!")
        print(f"Build number: {job_info.get('number', 'N/A')}")
        print(f"Build result: {job_info.get('result', 'N/A')}")
        print(f"Build duration: {job_info.get('duration', 'N/A')} ms")
        
        print(f"\nTesting console log (parsed) for: {job_url}")
        console_log_parsed = await client.get_console_log(job_url, parse_errors=True)
        print(f"Parsed console log retrieved successfully!")
        print(f"Parsed console log length: {len(console_log_parsed)} characters")
        print("First 200 characters of parsed log:")
        print("-" * 20)
        print(console_log_parsed[:200])
        print("-" * 20)
        
        print(f"\nTesting console log (full) for: {job_url}")
        console_log_full = await client.get_console_log(job_url, parse_errors=False)
        print(f"Full console log retrieved successfully!")
        print(f"Full console log length: {len(console_log_full)} characters")
        print("Size comparison:")
        print(f"  Full log: {len(console_log_full):,} characters")
        print(f"  Parsed log: {len(console_log_parsed):,} characters")
        print(f"  Reduction: {((len(console_log_full) - len(console_log_parsed)) / len(console_log_full) * 100):.1f}%")
        
    except Exception as e:
        print(f"Jenkins connectivity test failed: {e}")
        print("This is expected if you haven't configured real Jenkins credentials.")
  

if __name__ == "__main__":
    asyncio.run(test_jenkins_client()) 