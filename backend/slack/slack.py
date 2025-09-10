"""
Slack API integration for fetching user messages with context and replies.

This module provides functionality to:
1. Search for messages mentioning a specific user
2. Fetch conversation history (previous and next messages)
3. Get replies to specific messages
4. Structure the data for easy consumption
"""

import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import requests
from dataclasses import dataclass
from dotenv import load_dotenv
from .exceptions import (
    SlackAPIError,
    SlackAuthenticationError,
    SlackRateLimitError,
    SlackNetworkError,
    SlackDataParsingError,
    map_slack_error
)

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class SlackMessage:
    """Data structure for a Slack message."""
    ts: str
    user: str
    text: str
    channel_id: str
    channel_name: str
    permalink: str
    message_type: str = "message"
    thread_ts: Optional[str] = None
    reply_count: Optional[int] = None


@dataclass
class MessageContext:
    """Data structure for message context including previous/next messages and replies."""
    original_message: SlackMessage
    previous_messages: List[SlackMessage]
    next_messages: List[SlackMessage]
    replies: List[SlackMessage]


class SlackAPI:
    """
    Slack API client for fetching user messages with context.
    
    This class implements the workflow described in the curl commands:
    1. Search for messages mentioning a user
    2. For each message, fetch context (previous/next messages)
    3. Fetch replies to each message
    4. Structure the data for API consumption
    """
    
    def __init__(self, token: Optional[str] = None):
        """
        Initialize the Slack API client.
        
        Args:
            token: Slack OAuth token. If not provided, will try to get from environment.
        """
        self.token = token or os.getenv('SLACK_OAUTH_TOKEN')
        if not self.token:
            raise ValueError("Slack OAuth token is required. Set SLACK_OAUTH_TOKEN environment variable.")
        
        self.base_url = "https://slack.com/api"
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        # Test the token on initialization
        self._validate_token()
    
    def _validate_token(self) -> None:
        """Validate the Slack token by making a test API call."""
        try:
            response = requests.get(
                f"{self.base_url}/auth.test",
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            if not data.get('ok'):
                error = data.get('error', 'Unknown error')
                logger.error(f"Slack token validation failed: {error}")
                raise SlackAuthenticationError(
                    f"Invalid Slack token: {error}",
                    error_code=error,
                    details=data
                )

            logger.info(f"Slack API initialized successfully for user: {data.get('user')}")

        except requests.Timeout:
            logger.error("Slack API validation timed out")
            raise SlackNetworkError("Slack API validation timed out")
        except requests.ConnectionError:
            logger.error("Failed to connect to Slack API")
            raise SlackNetworkError("Failed to connect to Slack API")
        except requests.RequestException as e:
            logger.error(f"Network error during Slack token validation: {e}")
            raise SlackNetworkError(f"Network error during token validation: {e}")
        except SlackAPIError:
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            logger.error(f"Unexpected error during token validation: {e}")
            raise SlackAPIError(f"Unexpected error during token validation: {e}")
    
    def search_user_messages(self, username: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Search for messages mentioning a specific user.
        
        Args:
            username: The username to search for (e.g., 'satya.prakash')
            limit: Maximum number of messages to return
            
        Returns:
            List of message data from Slack search API
        """
        try:
            # Construct search query - search for @username mentions
            query = f"@{username}"
            
            params = {
                "query": query,
                "sort": "timestamp",
                "count": limit
            }
            
            response = requests.get(
                f"{self.base_url}/search.messages",
                headers=self.headers,
                params=params,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            
            if not data.get('ok'):
                error = data.get('error', 'Unknown error')
                logger.error(f"Slack search API error: {error}")
                raise map_slack_error(data)

            messages = data.get('messages', {}).get('matches', [])
            logger.info(f"Found {len(messages)} messages mentioning @{username}")

            return messages

        except requests.Timeout:
            logger.error("Slack search API timed out")
            raise SlackNetworkError("Slack search API timed out")
        except requests.ConnectionError:
            logger.error("Failed to connect to Slack search API")
            raise SlackNetworkError("Failed to connect to Slack search API")
        except requests.RequestException as e:
            logger.error(f"Network error during message search: {e}")
            raise SlackNetworkError(f"Network error during message search: {e}")
        except SlackAPIError:
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            logger.error(f"Unexpected error during message search: {e}")
            raise SlackAPIError(f"Unexpected error during message search: {e}")
    
    def get_conversation_history(self, channel_id: str, message_ts: str, 
                               limit: int = 10, direction: str = "previous") -> List[Dict[str, Any]]:
        """
        Get conversation history around a specific message.
        
        Args:
            channel_id: The channel ID where the message is located
            message_ts: The timestamp of the reference message
            limit: Number of messages to fetch
            direction: "previous" for messages before, "next" for messages after
            
        Returns:
            List of message data from conversations.history API
        """
        try:
            params = {
                "channel": channel_id,
                "limit": limit,
                "inclusive": True
            }
            
            # Set the appropriate parameter based on direction
            if direction == "previous":
                params["latest"] = message_ts
            else:  # next
                params["oldest"] = message_ts
            
            response = requests.get(
                f"{self.base_url}/conversations.history",
                headers=self.headers,
                params=params,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            
            if not data.get('ok'):
                error = data.get('error', 'Unknown error')
                logger.error(f"Slack conversations.history API error: {error}")
                raise map_slack_error(data)

            messages = data.get('messages', [])
            logger.debug(f"Fetched {len(messages)} {direction} messages for channel {channel_id}")

            return messages

        except requests.Timeout:
            logger.error("Slack conversations.history API timed out")
            raise SlackNetworkError("Slack conversations.history API timed out")
        except requests.ConnectionError:
            logger.error("Failed to connect to Slack conversations.history API")
            raise SlackNetworkError("Failed to connect to Slack conversations.history API")
        except requests.RequestException as e:
            logger.error(f"Network error during conversation history fetch: {e}")
            raise SlackNetworkError(f"Network error during conversation history fetch: {e}")
        except SlackAPIError:
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            logger.error(f"Unexpected error during conversation history fetch: {e}")
            raise SlackAPIError(f"Unexpected error during conversation history fetch: {e}")
    
    def get_message_replies(self, channel_id: str, message_ts: str) -> List[Dict[str, Any]]:
        """
        Get replies to a specific message.
        
        Args:
            channel_id: The channel ID where the message is located
            message_ts: The timestamp of the message to get replies for
            
        Returns:
            List of reply message data from conversations.replies API
        """
        try:
            params = {
                "channel": channel_id,
                "ts": message_ts
            }
            
            response = requests.get(
                f"{self.base_url}/conversations.replies",
                headers=self.headers,
                params=params,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            
            if not data.get('ok'):
                error = data.get('error', 'Unknown error')
                logger.error(f"Slack conversations.replies API error: {error}")
                raise map_slack_error(data)

            messages = data.get('messages', [])
            # Remove the original message from replies (first message is always the original)
            replies = messages[1:] if len(messages) > 1 else []

            logger.debug(f"Fetched {len(replies)} replies for message {message_ts}")

            return replies

        except requests.Timeout:
            logger.error("Slack conversations.replies API timed out")
            raise SlackNetworkError("Slack conversations.replies API timed out")
        except requests.ConnectionError:
            logger.error("Failed to connect to Slack conversations.replies API")
            raise SlackNetworkError("Failed to connect to Slack conversations.replies API")
        except requests.RequestException as e:
            logger.error(f"Network error during message replies fetch: {e}")
            raise SlackNetworkError(f"Network error during message replies fetch: {e}")
        except SlackAPIError:
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            logger.error(f"Unexpected error during message replies fetch: {e}")
            raise SlackAPIError(f"Unexpected error during message replies fetch: {e}")

    def _parse_message(self, message_data: Dict[str, Any]) -> SlackMessage:
        """
        Parse raw message data into a SlackMessage object.

        Args:
            message_data: Raw message data from Slack API

        Returns:
            SlackMessage object
        """
        # Handle both search results and conversation messages
        channel_info = message_data.get('channel', {})
        if isinstance(channel_info, dict):
            channel_id = channel_info.get('id', '')
            channel_name = channel_info.get('name', '')
        else:
            # For conversation messages, channel might just be a string ID
            channel_id = str(channel_info) if channel_info else ''
            channel_name = ''

        return SlackMessage(
            ts=message_data.get('ts', ''),
            user=message_data.get('user', ''),
            text=message_data.get('text', ''),
            channel_id=channel_id,
            channel_name=channel_name,
            permalink=message_data.get('permalink', ''),
            thread_ts=message_data.get('thread_ts'),
            reply_count=message_data.get('reply_count', 0)
        )

    def get_user_messages_with_context(self, username: str,
                                     context_limit: int = 10,
                                     search_limit: int = 20) -> List[MessageContext]:
        """
        Get all messages mentioning a user along with their context and replies.

        This is the main method that implements the complete workflow:
        1. Search for messages mentioning the user
        2. For each message, fetch previous and next messages
        3. Fetch replies to each message
        4. Structure everything into MessageContext objects

        Args:
            username: The username to search for (e.g., 'satya.prakash')
            context_limit: Number of previous/next messages to fetch for context
            search_limit: Maximum number of initial messages to search for

        Returns:
            List of MessageContext objects containing messages with full context
        """
        try:
            logger.info(f"Starting message retrieval for user: {username}")

            # Step 1: Search for messages mentioning the user
            search_results = self.search_user_messages(username, search_limit)

            message_contexts = []

            for i, message_data in enumerate(search_results):
                try:
                    logger.info(f"Processing message {i+1}/{len(search_results)}")

                    # Parse the original message
                    original_message = self._parse_message(message_data)

                    # Skip if we don't have essential information
                    if not original_message.channel_id or not original_message.ts:
                        logger.warning(f"Skipping message with missing channel_id or ts")
                        continue

                    # Step 2: Get previous messages (context before)
                    previous_messages = []
                    try:
                        prev_data = self.get_conversation_history(
                            original_message.channel_id,
                            original_message.ts,
                            context_limit,
                            "previous"
                        )
                        previous_messages = [self._parse_message(msg) for msg in prev_data]
                    except Exception as e:
                        logger.warning(f"Failed to get previous messages: {e}")

                    # Step 3: Get next messages (context after)
                    next_messages = []
                    try:
                        next_data = self.get_conversation_history(
                            original_message.channel_id,
                            original_message.ts,
                            context_limit,
                            "next"
                        )
                        next_messages = [self._parse_message(msg) for msg in next_data]
                    except Exception as e:
                        logger.warning(f"Failed to get next messages: {e}")

                    # Step 4: Get replies to the message
                    replies = []
                    try:
                        reply_data = self.get_message_replies(
                            original_message.channel_id,
                            original_message.ts
                        )
                        replies = [self._parse_message(msg) for msg in reply_data]
                    except Exception as e:
                        logger.warning(f"Failed to get replies: {e}")

                    # Create the message context
                    context = MessageContext(
                        original_message=original_message,
                        previous_messages=previous_messages,
                        next_messages=next_messages,
                        replies=replies
                    )

                    message_contexts.append(context)

                except Exception as e:
                    logger.error(f"Failed to process message {i+1}: {e}")
                    continue

            logger.info(f"Successfully processed {len(message_contexts)} messages with context")
            return message_contexts

        except Exception as e:
            logger.error(f"Failed to get user messages with context: {e}")
            raise
