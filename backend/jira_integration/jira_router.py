"""
FastAPI router for JIRA issue data processing.

This router provides endpoints to fetch and process JIRA issue data,
reading configuration from environment variables.
"""

import os
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import common models
from common.models import AnalyzedItem, jira_result_to_analyzed_item

# Import JIRA modules
try:
    from . import JiraJSONProcessor, generate_jira_json_output, find_jira_keys_by_conditions
except ImportError:
    # Fallback for direct execution - load the module dynamically
    import importlib.util
    spec = importlib.util.spec_from_file_location("jira_main", os.path.join(os.path.dirname(__file__), "jira-main.py"))
    jira_main = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(jira_main)

    JiraJSONProcessor = jira_main.JiraJSONProcessor
    generate_jira_json_output = jira_main.generate_jira_json_output
    find_jira_keys_by_conditions = jira_main.find_jira_keys_by_conditions


class ErrorResponse(BaseModel):
    """Error response model."""
    success: bool
    error: str
    details: Optional[str] = None


# Create router
router = APIRouter(prefix="/jira", tags=["jira"])


def get_jira_config():
    """Get JIRA configuration from environment variables."""
    jira_server = os.getenv('JIRA_SERVER')
    username = os.getenv('USERNAME')
    api_token = os.getenv('API_TOKEN')
    
    if not jira_server:
        raise HTTPException(
            status_code=500, 
            detail="JIRA_SERVER environment variable is required"
        )
    
    if not username:
        raise HTTPException(
            status_code=500, 
            detail="USERNAME environment variable is required"
        )
    
    if not api_token:
        raise HTTPException(
            status_code=500, 
            detail="API_TOKEN environment variable is required"
        )
    
    return jira_server, username, api_token


@router.get("/issues", response_model=List[AnalyzedItem])
async def get_user_issues(
    limit: Optional[int] = Query(None, description="Maximum number of issues to return (applied after JIRA query limit of 10)")
):
    """
    Get processed JIRA issue data for the current user.

    Returns a list of analyzed items in the common format used across all integrations.
    Configuration is read from environment variables:
    - JIRA_SERVER: JIRA server URL
    - USERNAME: JIRA username
    - API_TOKEN: JIRA API token
    """
    try:
        # Validate configuration
        get_jira_config()

        # Validate limit if provided
        if limit is not None and (limit <= 0 or limit > 50):
            raise HTTPException(
                status_code=400,
                detail="Limit must be between 1 and 50"
            )

        # Generate JIRA JSON output
        results = generate_jira_json_output()

        # Apply limit if specified
        if limit is not None:
            results = results[:limit]

        # Convert to common AnalyzedItem format
        analyzed_items = []
        for result in results:
            analyzed_item = jira_result_to_analyzed_item(result)
            analyzed_items.append(analyzed_item)

        # Return list of analyzed items directly
        return analyzed_items

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch JIRA issues: {str(e)}"
        )


@router.get("/issues/specific", response_model=List[AnalyzedItem])
async def get_specific_issues(
    keys: str = Query(..., description="Comma-separated list of JIRA issue keys (e.g., 'CDM-123,CDM-456')")
):
    """
    Get processed JIRA issue data for specific issue keys.

    Returns a list of analyzed items in the common format used across all integrations.

    Args:
        keys: Comma-separated list of JIRA issue keys
    """
    try:
        # Validate configuration
        get_jira_config()

        # Parse issue keys
        issue_keys = [key.strip().upper() for key in keys.split(',') if key.strip()]

        if not issue_keys:
            raise HTTPException(
                status_code=400,
                detail="At least one JIRA issue key must be provided"
            )

        if len(issue_keys) > 20:
            raise HTTPException(
                status_code=400,
                detail="Maximum 20 issue keys allowed per request"
            )

        # Initialize processor and convert to JSON
        processor = JiraJSONProcessor()
        results = processor.convert_jira_to_json(issue_keys)

        # Convert to common AnalyzedItem format
        analyzed_items = []
        for result in results:
            analyzed_item = jira_result_to_analyzed_item(result)
            analyzed_items.append(analyzed_item)

        # Return list of analyzed items directly
        return analyzed_items

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process JIRA issues: {str(e)}"
        )


@router.get("/config")
async def get_config():
    """
    Get current JIRA configuration (without sensitive data).
    """
    try:
        jira_server, username, api_token = get_jira_config()
        
        return {
            "jira_server": jira_server,
            "username": username,
            "api_token_configured": bool(api_token)
        }
        
    except HTTPException as e:
        return {
            "error": e.detail,
            "jira_server": os.getenv('JIRA_SERVER'),
            "username": os.getenv('USERNAME'),
            "api_token_configured": bool(os.getenv('API_TOKEN'))
        }


@router.get("/health")
async def jira_health():
    """
    Health check for JIRA integration.
    """
    try:
        jira_server, username, _ = get_jira_config()

        # Test JIRA connection by trying to find issues
        keys = find_jira_keys_by_conditions()
        
        return {
            "status": "healthy",
            "jira_api": "connected",
            "configured_user": username,
            "jira_server": jira_server,
            "found_issues": len(keys)
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "jira_api": "disconnected"
        }
