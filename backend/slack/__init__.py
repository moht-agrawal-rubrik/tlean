"""
Slack integration package for message retrieval with context and replies.

This package provides:
- SlackAPI class for interacting with Slack Web API
- Pydantic models for data structure and validation
- FastAPI endpoints for REST API access
- Complete workflow for fetching messages with context
"""

from .slack import SlackAPI, SlackMessage, MessageContext
from .models import (
    SlackMessageModel,
    MessageContextModel,
    UserMessagesResponse,
    AnalyzedMessagesResponse,
    AnalyzedSlackMessageModel,
    ErrorResponse,
    SlackAPIStatus
)
from .endpoints import router
from .exceptions import (
    SlackAPIError,
    SlackAuthenticationError,
    SlackRateLimitError,
    SlackNetworkError,
    SlackDataParsingError
)
from .message_filter import MessageAttentionFilter, filter_messages_for_attention
from .llm_analyzer import SlackMessageAnalyzer, analyze_message_contexts

__all__ = [
    "SlackAPI",
    "SlackMessage",
    "MessageContext",
    "SlackMessageModel",
    "MessageContextModel",
    "UserMessagesResponse",
    "AnalyzedMessagesResponse",
    "AnalyzedSlackMessageModel",
    "ErrorResponse",
    "SlackAPIStatus",
    "SlackAPIError",
    "SlackAuthenticationError",
    "SlackRateLimitError",
    "SlackNetworkError",
    "SlackDataParsingError",
    "MessageAttentionFilter",
    "filter_messages_for_attention",
    "SlackMessageAnalyzer",
    "analyze_message_contexts",
    "router"
]
