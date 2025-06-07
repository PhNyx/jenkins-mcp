#!/usr/bin/env python3
"""
Jenkins Agent using Pydantic-ai
Provides console log fetching capabilities for Jenkins jobs as tools
"""

import asyncio
import json
import logging
import sys
from typing import Any, Dict, List, Optional, Annotated
import re
from urllib.parse import urlparse
import base64

import httpx
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext, tool


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class JenkinsConfig(BaseModel):
    """Configuration for Jenkins connection"""
    base_url: str = Field(..., description="Jenkins base URL")
    username: str = Field(..., description="Jenkins username")
    token: str = Field(..., description="Jenkins API token")


class JenkinsContext(BaseModel):
    """Context for Jenkins operations"""
    config: JenkinsConfig


class JenkinsClient:
    """Client for interacting with Jenkins API"""
    
    def __init__(self, config: JenkinsConfig):
        self.config = config
        self.base_url = config.base_url.rstrip('/')
        
        # Create auth header
        credentials = f"{config.username}:{config.token}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        self.headers = {
            "Authorization": f"Basic {encoded_credentials}",
            "Accept": "application/json",
        }
    
    async def get_console_log(self, job_url: str, build_number: Optional[int] = None) -> str:
        """
        Fetch console log from Jenkins job
        
        Args:
            job_url: Full Jenkins job URL or job path
            build_number: Specific build number (if None, gets latest build)
        
        Returns:
            Console log as string
        """
        try:
            # Parse the job URL to extract job path
            job_path = self._extract_job_path(job_url)
            
            # If no build number specified, get the latest build
            if build_number is None:
                build_number = await self._get_latest_build_number(job_path)
            
            # Construct console log URL
            console_url = f"{self.base_url}/job/{job_path}/{build_number}/consoleText"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(console_url, headers=self.headers, timeout=30.0)
                response.raise_for_status()
                return response.text
                
        except Exception as e:
            logger.error(f"Error fetching console log: {e}")
            raise Exception(f"Failed to fetch console log: {str(e)}")
    
    def _extract_job_path(self, job_url: str) -> str:
        """Extract job path from Jenkins URL"""
        # Handle various URL formats
        if job_url.startswith('http'):
            parsed = urlparse(job_url)
            path = parsed.path
            
            # Extract job path from URL path
            # Expected formats: /job/jobname/ or /job/folder/job/jobname/
            job_match = re.search(r'/job/([^/]+(?:/job/[^/]+)*)', path)
            if job_match:
                return job_match.group(1).replace('/job/', '/')
            else:
                raise ValueError(f"Cannot extract job path from URL: {job_url}")
        else:
            # Assume it's already a job path
            return job_url.strip('/')
    
    async def _get_latest_build_number(self, job_path: str) -> int:
        """Get the latest build number for a job"""
        job_api_url = f"{self.base_url}/job/{job_path}/api/json"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(job_api_url, headers=self.headers, timeout=10.0)
            response.raise_for_status()
            job_data = response.json()
            
            if 'lastBuild' not in job_data or job_data['lastBuild'] is None:
                raise Exception("No builds found for this job")
            
            return job_data['lastBuild']['number']
    
    async def get_job_info(self, job_url: str) -> dict:
        """Get basic job information"""
        try:
            job_path = self._extract_job_path(job_url)
            job_api_url = f"{self.base_url}/job/{job_path}/api/json"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(job_api_url, headers=self.headers, timeout=10.0)
                response.raise_for_status()
                return response.json()
                
        except Exception as e:
            logger.error(f"Error fetching job info: {e}")
            raise Exception(f"Failed to fetch job info: {str(e)}")


# Create the Jenkins agent
jenkins_agent = Agent(
    'openai:gpt-4o-mini',  # You can change this to any model you prefer
    deps_type=JenkinsContext,
    system_prompt="""You are a Jenkins assistant that helps users fetch console logs and job information.
    You have access to tools that can connect to Jenkins instances and retrieve build information.
    Always provide helpful and accurate information about Jenkins jobs and builds."""
)


@jenkins_agent.tool
async def fetch_jenkins_console_log(
    ctx: RunContext[JenkinsContext],
    jenkins_url: Annotated[str, Field(description="Jenkins base URL (e.g., https://jenkins.company.com)")],
    username: Annotated[str, Field(description="Jenkins username")],
    token: Annotated[str, Field(description="Jenkins API token")],
    job_url: Annotated[str, Field(description="Full Jenkins job URL or job path")],
    build_number: Annotated[Optional[int], Field(description="Specific build number (optional, defaults to latest)", ge=1)] = None,
) -> str:
    """Fetch console log from a Jenkins job build."""
    
    try:
        # Create Jenkins client with provided credentials
        config = JenkinsConfig(
            base_url=jenkins_url,
            username=username,
            token=token
        )
        client = JenkinsClient(config)
        
        # Fetch console log
        console_log = await client.get_console_log(job_url, build_number)
        
        return f"Console log for job {job_url} (build {build_number or 'latest'}):\n\n{console_log}"
        
    except Exception as e:
        return f"Error fetching console log: {str(e)}"


@jenkins_agent.tool
async def get_jenkins_job_info(
    ctx: RunContext[JenkinsContext],
    jenkins_url: Annotated[str, Field(description="Jenkins base URL (e.g., https://jenkins.company.com)")],
    username: Annotated[str, Field(description="Jenkins username")],
    token: Annotated[str, Field(description="Jenkins API token")],
    job_url: Annotated[str, Field(description="Full Jenkins job URL or job path")],
) -> str:
    """Get basic information about a Jenkins job."""
    
    try:
        # Create Jenkins client with provided credentials
        config = JenkinsConfig(
            base_url=jenkins_url,
            username=username,
            token=token
        )
        client = JenkinsClient(config)
        
        # Fetch job info
        job_info = await client.get_job_info(job_url)
        
        # Format the response nicely
        formatted_info = json.dumps(job_info, indent=2)
        
        return f"Job information for {job_url}:\n\n{formatted_info}"
        
    except Exception as e:
        return f"Error fetching job info: {str(e)}"


async def main():
    """Main entry point - can be used for testing the agent directly"""
    
    # Example of running the agent directly (for testing)
    context = JenkinsContext(config=JenkinsConfig(
        base_url="https://your-jenkins.com",
        username="your-username", 
        token="your-token"
    ))
    
    result = await jenkins_agent.run(
        "Get the console log for job https://jenkins.example.com/job/my-project/",
        deps=context
    )
    
    print(result.data)


if __name__ == "__main__":
    asyncio.run(main()) 