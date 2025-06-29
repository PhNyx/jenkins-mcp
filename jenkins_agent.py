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
import os
from dotenv import load_dotenv
import httpx
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from log_parser import extract_error_block

load_dotenv()

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
    
    async def get_console_log(self, job_url: str, build_number: Optional[int] = None, parse_errors: bool = True) -> str:
        """
        Fetch console log from Jenkins job
        
        Args:
            job_url: Full Jenkins job URL or job path
            build_number: Specific build number (if None, gets latest build)
            parse_errors: If True, extract only error-relevant sections (default: True)
        
        Returns:
            Console log as string (full or parsed based on parse_errors flag)
        """
        try:
            # Parse the job URL to extract job path and potential build number
            job_path, url_build_number = self._extract_job_path(job_url)
            
            # Use build number from URL if not explicitly provided
            if build_number is None:
                build_number = url_build_number
            
            # If still no build number, get the latest build
            if build_number is None:
                build_number = await self._get_latest_build_number(job_path)
            
            # Construct console log URL
            console_url = f"{self.base_url}/{job_path}/{build_number}/consoleText"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(console_url, headers=self.headers, timeout=30.0)
                response.raise_for_status()
                
                # Parse errors from the log if requested
                if parse_errors:
                    parsed_log = extract_error_block(response.text)
                    logger.info(f"Console log parsed: {len(response.text)} chars -> {len(parsed_log)} chars")
                    return parsed_log
                else:
                    return response.text
                
        except Exception as e:
            logger.error(f"Error fetching console log: {e}")
            raise Exception(f"Failed to fetch console log: {str(e)}")
    
    def _extract_job_path(self, job_url: str) -> tuple[str, Optional[int]]:
        """Extract job path and build number from Jenkins URL"""
        # Handle various URL formats
        if job_url.startswith('http'):
            parsed = urlparse(job_url)
            path = parsed.path.rstrip('/')
            
            # Check if URL ends with a build number
            build_number = None
            build_match = re.search(r'/(\d+)$', path)
            if build_match:
                build_number = int(build_match.group(1))
                # Remove build number from path for job path extraction  
                path = path[:build_match.start()]
            
            # Extract the full job path including any prefix
            # Look for the pattern that starts with /job/ and capture everything up to the end or build number
            if '/job/' in path:
                # Find the start of the job structure
                job_start = path.find('/job/')
                prefix = path[:job_start] if job_start > 0 else ''
                job_portion = path[job_start:]
                
                # Extract just the job names, removing /job/ separators
                job_match = re.search(r'/job/([^/]+(?:/job/[^/]+)*)', job_portion)
                if job_match:
                    job_path = job_match.group(1).replace('/job/', '/')
                    full_path = prefix + '/job/' + job_path.replace('/', '/job/')
                    return full_path.lstrip('/'), build_number
                else:
                    raise ValueError(f"Cannot extract job path from URL: {job_url}")
            else:
                raise ValueError(f"URL does not contain job path: {job_url}")
        else:
            # Assume it's already a job path
            return job_url.strip('/'), None
    
    async def _get_latest_build_number(self, job_path: str) -> int:
        """Get the latest build number for a job"""
        job_api_url = f"{self.base_url}/{job_path}/api/json"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(job_api_url, headers=self.headers, timeout=10.0)
            response.raise_for_status()
            job_data = response.json()
            
            if 'lastBuild' not in job_data or job_data['lastBuild'] is None:
                raise Exception("No builds found for this job")
            
            return job_data['lastBuild']['number']
    
    async def get_job_info(self, job_url: str) -> dict:
        """Get basic job information or build information if URL contains build number"""
        try:
            job_path, build_number = self._extract_job_path(job_url)
            
            # If URL contains a build number, get build info instead of job info
            if build_number is not None:
                job_api_url = f"{self.base_url}/{job_path}/{build_number}/api/json"
            else:
                job_api_url = f"{self.base_url}/{job_path}/api/json"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(job_api_url, headers=self.headers, timeout=10.0)
                response.raise_for_status()
                return response.json()
                
        except Exception as e:
            logger.error(f"Error fetching job info: {e}")
            raise Exception(f"Failed to fetch job info: {str(e)}")


# Create the Jenkins agent (only when needed and API key is available)
jenkins_agent = None

try:
    # Try to create the agent - will fail if no OpenAI API key
    jenkins_agent = Agent(
        'openai:gpt-4.1',  # You can change this to any model you prefer
        deps_type=JenkinsContext,
        system_prompt="""You are a Jenkins assistant that helps users fetch console logs and job information.
        You have access to tools that can connect to Jenkins instances and retrieve build information.
        Always provide helpful and accurate information about Jenkins jobs and builds."""
    )
except Exception:
    # Agent creation failed - probably no API key
    # This is fine for testing just the JenkinsClient
    jenkins_agent = None


# Tool functions - only registered if agent exists
if jenkins_agent is not None:
    @jenkins_agent.tool
    async def fetch_jenkins_console_log_tool(
        ctx: RunContext[JenkinsContext],
        jenkins_url: Annotated[str, Field(description="Jenkins base URL (e.g., https://jenkins.company.com)")],
        username: Annotated[str, Field(description="Jenkins username")],
        token: Annotated[str, Field(description="Jenkins API token")],
        job_url: Annotated[str, Field(description="Full Jenkins job URL or job path")],
        build_number: Annotated[Optional[int], Field(description="Specific build number (optional, defaults to latest)", ge=1)] = None,
        parse_errors: Annotated[bool, Field(description="Extract only error-relevant sections (default: True)")] = True,
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
            console_log = await client.get_console_log(job_url, build_number, parse_errors)
            
            log_type = "parsed error sections" if parse_errors else "full log"
            return f"Console log ({log_type}) for job {job_url} (build {build_number or 'latest'}):\n\n{console_log}"
            
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
        base_url=os.getenv('JENKINS_URL'),
        username=os.getenv('JENKINS_USERNAME'), 
        token=os.getenv('JENKINS_TOKEN')
    ))
    
    result = await jenkins_agent.run(
        "Get the console log for job.",
        deps=context
    )
    
    print(result.data)


if __name__ == "__main__":
    asyncio.run(main()) 