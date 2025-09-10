"""
Custom exceptions for Slack API integration.

This module defines custom exception classes for better error handling
and more specific error reporting in the Slack integration.
"""

from typing import Optional, Dict, Any


class SlackAPIError(Exception):
    """Base exception for Slack API related errors."""
    
    def __init__(self, message: str, error_code: Optional[str] = None, 
                 details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class SlackAuthenticationError(SlackAPIError):
    """Exception raised when Slack authentication fails."""
    
    def __init__(self, message: str = "Slack authentication failed", 
                 error_code: Optional[str] = None, 
                 details: Optional[Dict[str, Any]] = None):
        super().__init__(message, error_code, details)


class SlackRateLimitError(SlackAPIError):
    """Exception raised when Slack API rate limit is exceeded."""
    
    def __init__(self, message: str = "Slack API rate limit exceeded", 
                 retry_after: Optional[int] = None,
                 error_code: Optional[str] = None, 
                 details: Optional[Dict[str, Any]] = None):
        self.retry_after = retry_after
        super().__init__(message, error_code, details)


class SlackChannelNotFoundError(SlackAPIError):
    """Exception raised when a Slack channel is not found or not accessible."""
    
    def __init__(self, channel_id: str, 
                 message: Optional[str] = None,
                 error_code: Optional[str] = None, 
                 details: Optional[Dict[str, Any]] = None):
        self.channel_id = channel_id
        if message is None:
            message = f"Channel {channel_id} not found or not accessible"
        super().__init__(message, error_code, details)


class SlackMessageNotFoundError(SlackAPIError):
    """Exception raised when a Slack message is not found."""
    
    def __init__(self, message_ts: str, channel_id: Optional[str] = None,
                 message: Optional[str] = None,
                 error_code: Optional[str] = None, 
                 details: Optional[Dict[str, Any]] = None):
        self.message_ts = message_ts
        self.channel_id = channel_id
        if message is None:
            message = f"Message {message_ts} not found"
            if channel_id:
                message += f" in channel {channel_id}"
        super().__init__(message, error_code, details)


class SlackUserNotFoundError(SlackAPIError):
    """Exception raised when a Slack user is not found."""
    
    def __init__(self, username: str, 
                 message: Optional[str] = None,
                 error_code: Optional[str] = None, 
                 details: Optional[Dict[str, Any]] = None):
        self.username = username
        if message is None:
            message = f"User {username} not found"
        super().__init__(message, error_code, details)


class SlackPermissionError(SlackAPIError):
    """Exception raised when insufficient permissions for Slack API operation."""
    
    def __init__(self, operation: str, 
                 message: Optional[str] = None,
                 error_code: Optional[str] = None, 
                 details: Optional[Dict[str, Any]] = None):
        self.operation = operation
        if message is None:
            message = f"Insufficient permissions for operation: {operation}"
        super().__init__(message, error_code, details)


class SlackNetworkError(SlackAPIError):
    """Exception raised when network-related errors occur with Slack API."""
    
    def __init__(self, message: str = "Network error communicating with Slack API", 
                 error_code: Optional[str] = None, 
                 details: Optional[Dict[str, Any]] = None):
        super().__init__(message, error_code, details)


class SlackDataParsingError(SlackAPIError):
    """Exception raised when parsing Slack API response data fails."""
    
    def __init__(self, data_type: str, 
                 message: Optional[str] = None,
                 error_code: Optional[str] = None, 
                 details: Optional[Dict[str, Any]] = None):
        self.data_type = data_type
        if message is None:
            message = f"Failed to parse {data_type} data from Slack API response"
        super().__init__(message, error_code, details)


def map_slack_error(error_response: Dict[str, Any]) -> SlackAPIError:
    """
    Map Slack API error response to appropriate exception.
    
    Args:
        error_response: Error response from Slack API
        
    Returns:
        Appropriate SlackAPIError subclass
    """
    error_code = error_response.get('error', 'unknown_error')
    error_message = error_response.get('error', 'Unknown Slack API error')
    
    # Map common Slack error codes to specific exceptions
    error_mapping = {
        'invalid_auth': SlackAuthenticationError,
        'account_inactive': SlackAuthenticationError,
        'token_revoked': SlackAuthenticationError,
        'no_permission': SlackPermissionError,
        'rate_limited': SlackRateLimitError,
        'channel_not_found': SlackChannelNotFoundError,
        'user_not_found': SlackUserNotFoundError,
        'message_not_found': SlackMessageNotFoundError,
        'not_in_channel': SlackPermissionError,
    }
    
    exception_class = error_mapping.get(error_code, SlackAPIError)
    
    return exception_class(
        message=error_message,
        error_code=error_code,
        details=error_response
    )
