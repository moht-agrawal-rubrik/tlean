"""
Message filtering logic to identify Slack messages that need user attention.

This module provides functionality to filter out messages that have already been
responded to or resolved, focusing only on messages that require user action.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from .slack import MessageContext, SlackMessage

logger = logging.getLogger(__name__)


class MessageAttentionFilter:
    """
    Filter to identify messages that need user attention.
    
    This class analyzes message contexts to determine if a message requires
    user attention or if it has already been addressed/resolved.
    """
    
    def __init__(self, target_user_id: str):
        """
        Initialize the filter with the target user ID.
        
        Args:
            target_user_id: The user ID to check for responses and attention needs
        """
        self.target_user_id = target_user_id
    
    def filter_messages_needing_attention(
        self, 
        message_contexts: List[MessageContext],
        max_age_days: int = 30
    ) -> List[MessageContext]:
        """
        Filter message contexts to only include those needing user attention.
        
        Args:
            message_contexts: List of MessageContext objects to filter
            max_age_days: Maximum age of messages to consider (default: 30 days)
            
        Returns:
            List of MessageContext objects that need user attention
        """
        filtered_contexts = []
        
        for context in message_contexts:
            try:
                if self._needs_attention(context, max_age_days):
                    filtered_contexts.append(context)
                    logger.debug(f"Message {context.original_message.ts} needs attention")
                else:
                    logger.debug(f"Message {context.original_message.ts} does not need attention")
                    
            except Exception as e:
                logger.warning(f"Error filtering message {context.original_message.ts}: {e}")
                # Include message if we can't determine - better to show than miss
                filtered_contexts.append(context)
        
        logger.info(f"Filtered {len(message_contexts)} messages down to {len(filtered_contexts)} needing attention")
        return filtered_contexts
    
    def _needs_attention(self, context: MessageContext, max_age_days: int) -> bool:
        """
        Determine if a message context needs user attention.
        
        Args:
            context: MessageContext to analyze
            max_age_days: Maximum age to consider
            
        Returns:
            True if the message needs attention, False otherwise
        """
        original_msg = context.original_message
        
        # Check 1: Message age - skip very old messages
        if not self._is_recent_enough(original_msg, max_age_days):
            logger.debug(f"Message {original_msg.ts} is too old")
            return False
        
        # Check 2: User already responded in replies
        if self._user_responded_in_replies(context.replies):
            logger.debug(f"User already responded in replies to {original_msg.ts}")
            return False
        
        # Check 3: User responded in subsequent conversation
        if self._user_responded_in_next_messages(context.next_messages):
            logger.debug(f"User responded in subsequent messages after {original_msg.ts}")
            return False
        
        # Check 4: Message appears to be resolved based on content
        if self._appears_resolved(context):
            logger.debug(f"Message {original_msg.ts} appears to be resolved")
            return False
        
        # Check 5: No recent activity (conversation died)
        if self._conversation_inactive(context):
            logger.debug(f"Conversation for {original_msg.ts} appears inactive")
            return False
        
        # If none of the above conditions are met, the message likely needs attention
        return True
    
    def _is_recent_enough(self, message: SlackMessage, max_age_days: int) -> bool:
        """Check if message is recent enough to be relevant."""
        try:
            # Convert Slack timestamp to datetime
            message_time = datetime.fromtimestamp(float(message.ts))
            cutoff_time = datetime.now() - timedelta(days=max_age_days)
            return message_time > cutoff_time
        except (ValueError, TypeError):
            logger.warning(f"Could not parse timestamp {message.ts}")
            return True  # Include if we can't parse
    
    def _user_responded_in_replies(self, replies: List[SlackMessage]) -> bool:
        """Check if the target user responded in the replies."""
        for reply in replies:
            if reply.user == self.target_user_id:
                return True
        return False
    
    def _user_responded_in_next_messages(self, next_messages: List[SlackMessage]) -> bool:
        """Check if the target user responded in subsequent messages."""
        for msg in next_messages:
            if msg.user == self.target_user_id:
                return True
        return False
    
    def _appears_resolved(self, context: MessageContext) -> bool:
        """
        Check if the conversation appears to be resolved based on content analysis.
        
        This looks for resolution indicators in the text content.
        """
        resolution_indicators = [
            "done", "completed", "finished", "resolved", "fixed", "solved",
            "thanks", "thank you", "got it", "understood", "perfect",
            "sounds good", "looks good", "approved", "lgtm", "ship it"
        ]
        
        # Check replies for resolution indicators
        for reply in context.replies:
            text_lower = reply.text.lower()
            if any(indicator in text_lower for indicator in resolution_indicators):
                return True
        
        # Check next messages for resolution indicators
        for msg in context.next_messages:
            text_lower = msg.text.lower()
            if any(indicator in text_lower for indicator in resolution_indicators):
                return True
        
        return False
    
    def _conversation_inactive(self, context: MessageContext, inactive_days: int = 7) -> bool:
        """
        Check if the conversation has been inactive for too long.
        
        Args:
            context: MessageContext to check
            inactive_days: Number of days to consider as inactive
            
        Returns:
            True if conversation appears inactive
        """
        try:
            # Find the most recent activity timestamp
            latest_ts = float(context.original_message.ts)
            
            # Check replies for latest activity
            for reply in context.replies:
                reply_ts = float(reply.ts)
                if reply_ts > latest_ts:
                    latest_ts = reply_ts
            
            # Check next messages for latest activity
            for msg in context.next_messages:
                msg_ts = float(msg.ts)
                if msg_ts > latest_ts:
                    latest_ts = msg_ts
            
            # Check if latest activity is too old
            latest_time = datetime.fromtimestamp(latest_ts)
            cutoff_time = datetime.now() - timedelta(days=inactive_days)
            
            return latest_time < cutoff_time
            
        except (ValueError, TypeError):
            logger.warning("Could not parse timestamps for activity check")
            return False  # Don't filter out if we can't determine
    
    def get_attention_score(self, context: MessageContext) -> float:
        """
        Calculate an attention score for a message context.
        
        Higher scores indicate messages that need more urgent attention.
        
        Args:
            context: MessageContext to score
            
        Returns:
            Float score between 0.0 and 1.0
        """
        score = 0.0
        
        try:
            # Base score for being mentioned
            score += 0.3
            
            # Boost for recent messages
            message_age_hours = (datetime.now() - datetime.fromtimestamp(float(context.original_message.ts))).total_seconds() / 3600
            if message_age_hours < 24:
                score += 0.3
            elif message_age_hours < 72:
                score += 0.2
            elif message_age_hours < 168:  # 1 week
                score += 0.1
            
            # Boost for questions or requests
            original_text = context.original_message.text.lower()
            if any(word in original_text for word in ["?", "can you", "could you", "please", "need", "help"]):
                score += 0.2
            
            # Boost for follow-up messages
            if any(word in original_text for word in ["update", "status", "progress", "any news"]):
                score += 0.2
            
            # Reduce score if there are many replies (active discussion)
            if len(context.replies) > 3:
                score -= 0.1
            
            # Reduce score if user has been active in the thread
            user_reply_count = sum(1 for reply in context.replies if reply.user == self.target_user_id)
            if user_reply_count > 0:
                score -= 0.2 * user_reply_count
            
            # Ensure score is between 0 and 1
            return max(0.0, min(1.0, score))
            
        except Exception as e:
            logger.warning(f"Error calculating attention score: {e}")
            return 0.5  # Default moderate score


def filter_messages_for_attention(
    message_contexts: List[MessageContext],
    target_user_id: str,
    max_age_days: int = 30
) -> List[MessageContext]:
    """
    Convenience function to filter messages that need user attention.
    
    Args:
        message_contexts: List of MessageContext objects
        target_user_id: User ID to check for attention needs
        max_age_days: Maximum age of messages to consider
        
    Returns:
        Filtered list of MessageContext objects needing attention
    """
    filter_instance = MessageAttentionFilter(target_user_id)
    return filter_instance.filter_messages_needing_attention(message_contexts, max_age_days)
