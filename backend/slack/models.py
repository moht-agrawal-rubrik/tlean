"""
Pydantic models for Slack API responses and data structures.

This module defines the data models used for parsing and structuring
Slack API responses and creating consistent API responses.
"""

from typing import List, Optional, Dict, Any, TYPE_CHECKING
from datetime import datetime
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from .slack import SlackMessage, MessageContext


class SlackChannel(BaseModel):
    """Model for Slack channel information."""
    id: str
    name: Optional[str] = None
    is_channel: Optional[bool] = None
    is_group: Optional[bool] = None
    is_im: Optional[bool] = None
    is_mpim: Optional[bool] = None
    is_private: Optional[bool] = None


class SlackUser(BaseModel):
    """Model for Slack user information."""
    id: str
    username: Optional[str] = None
    display_name: Optional[str] = None
    real_name: Optional[str] = None


class SlackMessageBlock(BaseModel):
    """Model for Slack message block elements."""
    type: str
    block_id: Optional[str] = None
    elements: Optional[List[Dict[str, Any]]] = None


class SlackMessageModel(BaseModel):
    """Pydantic model for a Slack message."""
    ts: str = Field(..., description="Message timestamp")
    user: str = Field(..., description="User ID who sent the message")
    text: str = Field(..., description="Message text content")
    channel_id: str = Field(..., description="Channel ID where message was sent")
    channel_name: Optional[str] = Field(None, description="Channel name")
    permalink: Optional[str] = Field(None, description="Permanent link to message")
    message_type: str = Field(default="message", description="Type of message")
    thread_ts: Optional[str] = Field(None, description="Thread timestamp if message is in a thread")
    reply_count: Optional[int] = Field(None, description="Number of replies to this message")
    blocks: Optional[List[SlackMessageBlock]] = Field(None, description="Message blocks for rich formatting")
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class MessageContextModel(BaseModel):
    """Pydantic model for message context including related messages."""
    original_message: SlackMessageModel = Field(..., description="The main message")
    previous_messages: List[SlackMessageModel] = Field(
        default_factory=list, 
        description="Messages that came before the original message"
    )
    next_messages: List[SlackMessageModel] = Field(
        default_factory=list, 
        description="Messages that came after the original message"
    )
    replies: List[SlackMessageModel] = Field(
        default_factory=list, 
        description="Replies to the original message"
    )
    
    @property
    def total_related_messages(self) -> int:
        """Get total count of all related messages."""
        return len(self.previous_messages) + len(self.next_messages) + len(self.replies)


class UserMessagesResponse(BaseModel):
    """Response model for the user messages API endpoint."""
    user_id: str = Field(..., description="The user ID that was searched for")
    username: str = Field(..., description="The username that was searched for")
    total_messages_found: int = Field(..., description="Total number of messages found")
    messages_with_context: List[MessageContextModel] = Field(
        ..., 
        description="List of messages with their context and replies"
    )
    search_parameters: Dict[str, Any] = Field(
        default_factory=dict, 
        description="Parameters used for the search"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now, 
        description="When this response was generated"
    )
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SlackSearchResponse(BaseModel):
    """Model for Slack search.messages API response."""
    ok: bool
    query: str
    messages: Dict[str, Any]


class SlackConversationHistoryResponse(BaseModel):
    """Model for Slack conversations.history API response."""
    ok: bool
    messages: List[Dict[str, Any]]
    has_more: Optional[bool] = None
    pin_count: Optional[int] = None
    response_metadata: Optional[Dict[str, Any]] = None


class SlackConversationRepliesResponse(BaseModel):
    """Model for Slack conversations.replies API response."""
    ok: bool
    messages: List[Dict[str, Any]]
    has_more: Optional[bool] = None


class ErrorResponse(BaseModel):
    """Model for error responses."""
    error: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(None, description="Error code if available")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    timestamp: datetime = Field(
        default_factory=datetime.now, 
        description="When this error occurred"
    )
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SlackAPIStatus(BaseModel):
    """Model for Slack API status and health check."""
    status: str = Field(..., description="API status")
    authenticated: bool = Field(..., description="Whether authentication is successful")
    user_info: Optional[Dict[str, Any]] = Field(None, description="Authenticated user information")
    timestamp: datetime = Field(
        default_factory=datetime.now, 
        description="Status check timestamp"
    )
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# Utility functions for converting between internal models and Pydantic models

def slack_message_to_model(message: 'SlackMessage') -> SlackMessageModel:
    """Convert internal SlackMessage to Pydantic model."""
    return SlackMessageModel(
        ts=message.ts,
        user=message.user,
        text=message.text,
        channel_id=message.channel_id,
        channel_name=message.channel_name,
        permalink=message.permalink,
        message_type=message.message_type,
        thread_ts=message.thread_ts,
        reply_count=message.reply_count
    )


def message_context_to_model(context: 'MessageContext') -> MessageContextModel:
    """Convert internal MessageContext to Pydantic model."""
    return MessageContextModel(
        original_message=slack_message_to_model(context.original_message),
        previous_messages=[slack_message_to_model(msg) for msg in context.previous_messages],
        next_messages=[slack_message_to_model(msg) for msg in context.next_messages],
        replies=[slack_message_to_model(msg) for msg in context.replies]
    )
