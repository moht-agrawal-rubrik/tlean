"""
FastAPI router for GitHub PR data processing.

This router provides endpoints to fetch and process GitHub PR data,
reading configuration from environment variables.
"""

import os
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import GitHub modules
try:
    from github.github_candidate_generator import GitHubCandidateGenerator
except ImportError:
    try:
        from github_candidate_generator import GitHubCandidateGenerator
    except ImportError:
        raise ImportError("Could not import GitHubCandidateGenerator. Make sure the github module is available.")


# Response models
class ProcessedPRData(BaseModel):
    """Model for processed PR data."""
    source: str
    link: str
    timestamp: str
    title: str
    long_summary: str
    action_items: List[str]
    score: float


class GitHubResponse(BaseModel):
    """Response model for GitHub endpoints."""
    success: bool
    message: str
    data: List[ProcessedPRData]
    total_count: int


class ErrorResponse(BaseModel):
    """Error response model."""
    success: bool
    error: str
    details: Optional[str] = None


# Create router
router = APIRouter(prefix="/github", tags=["github"])


def get_github_config():
    """Get GitHub configuration from environment variables."""
    github_token = os.getenv('GITHUB_TOKEN')
    github_username = os.getenv('GITHUB_USERNAME')
    github_limit = int(os.getenv('GITHUB_LIMIT', '10'))  # Default to 10 if not set
    
    if not github_token:
        raise HTTPException(
            status_code=500, 
            detail="GITHUB_TOKEN environment variable is required"
        )
    
    if not github_username:
        raise HTTPException(
            status_code=500, 
            detail="GITHUB_USERNAME environment variable is required"
        )
    
    return github_token, github_username, github_limit


@router.get("/prs", response_model=GitHubResponse)
async def get_user_prs(
    state: str = Query("open", description="PR state: open, closed, or all"),
    limit: Optional[int] = Query(None, description="Override default limit from environment")
):
    """
    Get processed PR data for the configured GitHub user.
    
    Returns only the processed data (not raw data) in JSON format.
    Configuration is read from environment variables:
    - GITHUB_TOKEN: GitHub personal access token
    - GITHUB_USERNAME: GitHub username to fetch PRs for
    - GITHUB_LIMIT: Default limit for number of PRs (can be overridden by query param)
    """
    try:
        # Get configuration
        github_token, github_username, default_limit = get_github_config()
        
        # Use provided limit or default from environment
        fetch_limit = limit if limit is not None else default_limit
        
        # Validate limit
        if fetch_limit <= 0 or fetch_limit > 100:
            raise HTTPException(
                status_code=400,
                detail="Limit must be between 1 and 100"
            )
        
        # Initialize generator
        generator = GitHubCandidateGenerator(github_token)
        
        # Fetch user PRs
        candidates = generator.fetch_user_prs(
            username=github_username,
            state=state,
            limit=fetch_limit
        )
        
        # Extract only processed data
        processed_items = []
        for candidate in candidates:
            processed_data = candidate.get("processed_data", {})
            if processed_data:
                processed_items.append(ProcessedPRData(**processed_data))
        
        return GitHubResponse(
            success=True,
            message=f"Successfully fetched {len(processed_items)} PRs for user {github_username}",
            data=processed_items,
            total_count=len(processed_items)
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch GitHub PRs: {str(e)}"
        )


@router.get("/prs/raw", response_model=Dict[str, Any])
async def get_user_prs_raw(
    state: str = Query("open", description="PR state: open, closed, or all"),
    limit: Optional[int] = Query(None, description="Override default limit from environment")
):
    """
    Get complete PR data (both raw and processed) for the configured GitHub user.
    
    This endpoint returns the full candidate data including raw GitHub data.
    """
    try:
        # Get configuration
        github_token, github_username, default_limit = get_github_config()
        
        # Use provided limit or default from environment
        fetch_limit = limit if limit is not None else default_limit
        
        # Validate limit
        if fetch_limit <= 0 or fetch_limit > 100:
            raise HTTPException(
                status_code=400,
                detail="Limit must be between 1 and 100"
            )
        
        # Initialize generator
        generator = GitHubCandidateGenerator(github_token)
        
        # Fetch user PRs
        candidates = generator.fetch_user_prs(
            username=github_username,
            state=state,
            limit=fetch_limit
        )
        
        return {
            "success": True,
            "message": f"Successfully fetched {len(candidates)} PRs for user {github_username}",
            "data": candidates,
            "total_count": len(candidates)
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch GitHub PRs: {str(e)}"
        )


@router.get("/config")
async def get_config():
    """
    Get current GitHub configuration (without sensitive data).
    """
    try:
        github_token, github_username, github_limit = get_github_config()
        
        return {
            "github_username": github_username,
            "github_limit": github_limit,
            "github_token_configured": bool(github_token)
        }
        
    except HTTPException as e:
        return {
            "error": e.detail,
            "github_username": os.getenv('GITHUB_USERNAME'),
            "github_limit": os.getenv('GITHUB_LIMIT'),
            "github_token_configured": bool(os.getenv('GITHUB_TOKEN'))
        }


@router.get("/health")
async def github_health():
    """
    Health check for GitHub integration.
    """
    try:
        github_token, github_username, github_limit = get_github_config()
        
        # Test GitHub API connection
        generator = GitHubCandidateGenerator(github_token)
        
        # Make a simple API call to test connectivity
        test_url = f"https://api.github.com/user"
        response = generator.session.get(test_url)
        response.raise_for_status()
        
        return {
            "status": "healthy",
            "github_api": "connected",
            "configured_user": github_username,
            "default_limit": github_limit
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "github_api": "disconnected"
        }
