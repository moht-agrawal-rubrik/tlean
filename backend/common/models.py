"""
Common models for all integrations (GitHub, Slack, etc.).

This module defines the standardized response format that all integrations
should use for analyzed items (PRs, messages, issues, etc.).
"""

from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class AnalyzedItem(BaseModel):
    """
    Common model for analyzed items across all integrations.
    
    This standardized format is used for:
    - GitHub PRs
    - Slack messages  
    - JIRA issues
    - Any other integration items
    """
    source: str = Field(..., description="Source platform (github, slack, jira, etc.)")
    link: str = Field(..., description="Direct link to the item")
    timestamp: str = Field(..., description="ISO formatted timestamp")
    title: str = Field(..., description="Brief descriptive title")
    long_summary: str = Field(..., description="Detailed summary of the item")
    action_items: List[str] = Field(default_factory=list, description="List of action items")
    score: float = Field(..., ge=0.0, le=1.0, description="Attention score between 0.0 and 1.0")
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class AnalyzedItemsResponse(BaseModel):
    """
    Common response model for analyzed items from any integration.
    
    This standardized format wraps the list of analyzed items with metadata.
    """
    source: str = Field(..., description="Source platform (github, slack, jira, etc.)")
    user_identifier: str = Field(..., description="User identifier (username, email, etc.)")
    total_items_found: int = Field(..., description="Total number of items found initially")
    items_needing_attention: int = Field(..., description="Number of items that need attention")
    analyzed_items: List[AnalyzedItem] = Field(..., description="List of analyzed items")
    analysis_timestamp: datetime = Field(
        default_factory=datetime.now,
        description="When this analysis was performed"
    )
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# Helper functions for converting between formats

def create_analyzed_item(
    source: str,
    link: str,
    timestamp: str,
    title: str,
    long_summary: str,
    action_items: List[str],
    score: float
) -> AnalyzedItem:
    """
    Helper function to create an AnalyzedItem.
    
    Args:
        source: Source platform
        link: Direct link to the item
        timestamp: ISO formatted timestamp
        title: Brief descriptive title
        long_summary: Detailed summary
        action_items: List of action items
        score: Attention score (0.0-1.0)
        
    Returns:
        AnalyzedItem instance
    """
    return AnalyzedItem(
        source=source,
        link=link,
        timestamp=timestamp,
        title=title,
        long_summary=long_summary,
        action_items=action_items,
        score=score
    )


def create_analyzed_items_response(
    source: str,
    user_identifier: str,
    total_items_found: int,
    analyzed_items: List[AnalyzedItem]
) -> AnalyzedItemsResponse:
    """
    Helper function to create an AnalyzedItemsResponse.
    
    Args:
        source: Source platform
        user_identifier: User identifier
        total_items_found: Total items found initially
        analyzed_items: List of analyzed items
        
    Returns:
        AnalyzedItemsResponse instance
    """
    return AnalyzedItemsResponse(
        source=source,
        user_identifier=user_identifier,
        total_items_found=total_items_found,
        items_needing_attention=len(analyzed_items),
        analyzed_items=analyzed_items,
        analysis_timestamp=datetime.now()
    )


# Legacy conversion functions for backward compatibility

def slack_result_to_analyzed_item(slack_result: dict) -> AnalyzedItem:
    """
    Convert Slack analysis result to common AnalyzedItem format.
    
    Args:
        slack_result: Dictionary with Slack-specific fields
        
    Returns:
        AnalyzedItem instance
    """
    return AnalyzedItem(
        source="slack",
        link=slack_result.get("link", ""),
        timestamp=slack_result.get("timestamp", ""),
        title=slack_result.get("title", ""),
        long_summary=slack_result.get("long_summary", ""),
        action_items=slack_result.get("action_items", []),
        score=slack_result.get("score", 0.0)
    )


def github_result_to_analyzed_item(github_result: dict) -> AnalyzedItem:
    """
    Convert GitHub analysis result to common AnalyzedItem format.
    
    Args:
        github_result: Dictionary with GitHub-specific fields
        
    Returns:
        AnalyzedItem instance
    """
    return AnalyzedItem(
        source="github",
        link=github_result.get("link", ""),
        timestamp=github_result.get("timestamp", ""),
        title=github_result.get("title", ""),
        long_summary=github_result.get("long_summary", ""),
        action_items=github_result.get("action_items", []),
        score=github_result.get("score", 0.0)
    )
