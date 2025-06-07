#!/usr/bin/env python3
"""
Jenkins Client - Clean version for testing
Provides console log fetching capabilities for Jenkins jobs
"""

import asyncio
import json
import logging
import re
from typing import Optional
from urllib.parse import urlparse
import base64

import httpx
from pydantic import BaseModel, Field
from log_parser import extract_error_block

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class JenkinsConfig(BaseModel):
    """Configuration for Jenkins connection"""
    base_url: str = Field(..., description="Jenkins base URL")
    username: str = Field(..., description="Jenkins username")
    token: str = Field(..., description="Jenkins API token")


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


# Simple test function
async def test_client():
    """Simple test function"""
    config = JenkinsConfig(
        base_url="https://your-jenkins.com",
        username="your-username",
        token="your-token"
    )
    
    client = JenkinsClient(config)
    
    # Test URL parsing
    test_urls = [
        "https://jenkins.company.com/job/my-project/job/main/",
        "my-project/main",
        "simple-job"
    ]
    
    print("Testing URL parsing:")
    for url in test_urls:
        try:
            job_path, build_number = client._extract_job_path(url)
            print(f"  ✓ {url} -> Job Path: {job_path}")
            if build_number:
                print(f"    -> Build Number: {build_number}")
        except Exception as e:
            print(f"  ✗ {url} -> ERROR: {e}")


if __name__ == "__main__":
    asyncio.run(test_client()) 