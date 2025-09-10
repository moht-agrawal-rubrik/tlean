"""
FastAPI endpoints for Slack message retrieval API.

This module provides REST API endpoints for fetching Slack messages
with context and replies for specific users.
"""

import logging
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import JSONResponse

from .slack import SlackAPI
from .models import (
    UserMessagesResponse, 
    ErrorResponse, 
    SlackAPIStatus,
    message_context_to_model
)

# Configure logging
logger = logging.getLogger(__name__)

# Create router for Slack endpoints
router = APIRouter(prefix="/slack", tags=["slack"])


def get_slack_api() -> SlackAPI:
    """
    Dependency to get SlackAPI instance.
    
    Returns:
        SlackAPI instance
        
    Raises:
        HTTPException: If Slack API cannot be initialized
    """
    try:
        return SlackAPI()
    except ValueError as e:
        logger.error(f"Failed to initialize Slack API: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Slack API initialization failed: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error initializing Slack API: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error during Slack API initialization"
        )


@router.get("/health", response_model=SlackAPIStatus)
async def slack_health_check(slack_api: SlackAPI = Depends(get_slack_api)):
    """
    Health check endpoint for Slack API integration.
    
    Returns:
        SlackAPIStatus: Status of the Slack API connection
    """
    try:
        # The SlackAPI constructor already validates the token
        return SlackAPIStatus(
            status="healthy",
            authenticated=True,
            user_info={"message": "Slack API is properly configured and authenticated"},
            timestamp=datetime.now()
        )
    except Exception as e:
        logger.error(f"Slack health check failed: {e}")
        return SlackAPIStatus(
            status="unhealthy",
            authenticated=False,
            user_info={"error": str(e)},
            timestamp=datetime.now()
        )


@router.get("/user/{username}/messages", response_model=UserMessagesResponse)
async def get_user_messages(
    username: str,
    context_limit: int = Query(
        default=10, 
        ge=1, 
        le=50, 
        description="Number of previous/next messages to fetch for context"
    ),
    search_limit: int = Query(
        default=20, 
        ge=1, 
        le=100, 
        description="Maximum number of messages to search for"
    ),
    slack_api: SlackAPI = Depends(get_slack_api)
):
    """
    Get all messages mentioning a specific user with context and replies.
    
    This endpoint implements the complete workflow:
    1. Search for messages mentioning the user (@username)
    2. For each message, fetch previous and next messages for context
    3. Fetch replies to each message
    4. Return structured data with all related messages
    
    Args:
        username: The username to search for (e.g., 'satya.prakash')
        context_limit: Number of previous/next messages to fetch (1-50)
        search_limit: Maximum number of initial messages to search for (1-100)
        slack_api: Injected SlackAPI instance
        
    Returns:
        UserMessagesResponse: Structured response with messages and context
        
    Raises:
        HTTPException: If the request fails or user is not found
    """
    try:
        logger.info(f"Fetching messages for user: {username}")
        
        # Get messages with context using the SlackAPI
        message_contexts = slack_api.get_user_messages_with_context(
            username=username,
            context_limit=context_limit,
            search_limit=search_limit
        )
        
        # Convert to Pydantic models
        context_models = [message_context_to_model(ctx) for ctx in message_contexts]
        
        # Create response
        response = UserMessagesResponse(
            user_id=username,  # In this case, we're using username as identifier
            username=username,
            total_messages_found=len(context_models),
            messages_with_context=context_models,
            search_parameters={
                "context_limit": context_limit,
                "search_limit": search_limit,
                "search_query": f"@{username}"
            },
            timestamp=datetime.now()
        )
        
        logger.info(f"Successfully retrieved {len(context_models)} messages for {username}")
        return response
        
    except Exception as e:
        logger.error(f"Failed to get messages for user {username}: {e}")
        
        # Create error response
        error_response = ErrorResponse(
            error=f"Failed to retrieve messages for user {username}",
            details={"username": username, "error_message": str(e)},
            timestamp=datetime.now()
        )
        
        # Return appropriate HTTP status code based on error type
        if "not found" in str(e).lower() or "no messages" in str(e).lower():
            raise HTTPException(status_code=404, detail=error_response.model_dump())
        elif "unauthorized" in str(e).lower() or "token" in str(e).lower():
            raise HTTPException(status_code=401, detail=error_response.model_dump())
        elif "rate limit" in str(e).lower():
            raise HTTPException(status_code=429, detail=error_response.model_dump())
        else:
            raise HTTPException(status_code=500, detail=error_response.model_dump())


@router.get("/user/{username}/messages/summary")
async def get_user_messages_summary(
    username: str,
    search_limit: int = Query(
        default=20, 
        ge=1, 
        le=100, 
        description="Maximum number of messages to search for"
    ),
    slack_api: SlackAPI = Depends(get_slack_api)
):
    """
    Get a summary of messages mentioning a specific user without full context.
    
    This is a lighter endpoint that returns just the basic message information
    without fetching previous/next messages and replies.
    
    Args:
        username: The username to search for
        search_limit: Maximum number of messages to search for
        slack_api: Injected SlackAPI instance
        
    Returns:
        Summary of messages found
    """
    try:
        logger.info(f"Fetching message summary for user: {username}")
        
        # Get just the search results without context
        search_results = slack_api.search_user_messages(username, search_limit)
        
        # Create summary response
        summary = {
            "username": username,
            "total_messages_found": len(search_results),
            "messages": [
                {
                    "ts": msg.get("ts"),
                    "text": msg.get("text", "")[:100] + "..." if len(msg.get("text", "")) > 100 else msg.get("text", ""),
                    "channel": msg.get("channel", {}).get("name", "Unknown"),
                    "permalink": msg.get("permalink")
                }
                for msg in search_results
            ],
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"Successfully retrieved summary for {username}: {len(search_results)} messages")
        return summary
        
    except Exception as e:
        logger.error(f"Failed to get message summary for user {username}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve message summary: {str(e)}"
        )


@router.get("/search")
async def search_messages(
    query: str = Query(..., description="Search query for messages"),
    limit: int = Query(default=20, ge=1, le=100, description="Maximum number of results"),
    slack_api: SlackAPI = Depends(get_slack_api)
):
    """
    Generic message search endpoint.
    
    Args:
        query: Search query string
        limit: Maximum number of results to return
        slack_api: Injected SlackAPI instance
        
    Returns:
        Search results
    """
    try:
        logger.info(f"Searching messages with query: {query}")
        
        # Use the search functionality directly
        results = slack_api.search_user_messages(query.replace("@", ""), limit)
        
        return {
            "query": query,
            "total_results": len(results),
            "results": results,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Search failed for query '{query}': {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}"
        )
