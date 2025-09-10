import os
import json
from openai import OpenAI
from typing import List, Optional, Dict, Any
from dataclasses import dataclass


class SlackConversationAnalyzer:
    """
    A class to analyze Slack conversations with context and determine action items and problem summaries.
    """
    
    def __init__(self):
        """
        Initialize the OpenAI client with the same configuration as basic_endpoint_test.py
        """
        self.client = OpenAI(
            api_key=os.environ.get("OPENAI_API_KEY"), 
            base_url="https://basecamp.stark.rubrik.com"
        )
    
    def analyze_conversation_context(
        self, 
        target_message: Dict[str, Any],
        previous_messages: List[Dict[str, Any]] = None,
        next_messages: List[Dict[str, Any]] = None,
        replies: List[Dict[str, Any]] = None
    ) -> str:
        """
        Analyze a Slack conversation with full context to determine action items and problem summary.
        
        Args:
            target_message (Dict): The main message that the user was mentioned in (from sample_messages.json matches)
            previous_messages (List[Dict]): Previous messages for context (from sample_previous_4_messages.json)
            next_messages (List[Dict]): Next messages for context (from sample_next_4_messages.json)
            replies (List[Dict]): All replies to the target message (from sample_replies.json)
            
        Returns:
            str: The LLM analysis result in JSON format
        """
        # Format the conversation context for the LLM
        conversation_context = self._format_conversation_context(
            target_message, previous_messages, next_messages, replies
        )
        
        # Create the LLM request
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": """You are an expert Slack conversation analyzer designed to identify pending action items and summarize problems being discussed in Slack threads. You will receive structured JSON data representing a Slack conversation with full context.

**INPUT DATA STRUCTURE:**

You will receive a JSON object with the following structure:

```json
{
    "target_message": {
        // The main message where the user was mentioned - this is the focal point
        "iid": "unique-identifier",
        "team": "team-id", 
        "channel": {
            "id": "channel-id",
            "name": "channel-name",
            "is_channel": true/false,
            "is_group": true/false,
            "is_im": true/false,
            "is_private": true/false
        },
        "type": "message/im",
        "user": "user-id",
        "username": "username",
        "ts": "timestamp-string",
        "text": "message-content",
        "permalink": "slack-permalink",
        "blocks": [...] // Rich text formatting blocks
    },
    "previous_messages": [
        // Messages that occurred BEFORE the target message for context
        {
            "user": "user-id",
            "type": "message",
            "ts": "timestamp-string", 
            "client_msg_id": "message-id",
            "text": "message-content",
            "team": "team-id",
            "blocks": [...] // Rich text formatting
        }
    ],
    "next_messages": [
        // Messages that occurred AFTER the target message for context
        {
            "user": "user-id",
            "type": "message", 
            "ts": "timestamp-string",
            "client_msg_id": "message-id",
            "text": "message-content",
            "team": "team-id",
            "blocks": [...] // Rich text formatting
        }
    ],
    "replies": [
        // All replies specifically to the target message (threaded responses)
        {
            "user": "user-id",
            "type": "message",
            "ts": "timestamp-string",
            "client_msg_id": "message-id", 
            "text": "message-content",
            "team": "team-id",
            "thread_ts": "parent-thread-timestamp",
            "reply_count": number,
            "reply_users_count": number,
            "latest_reply": "timestamp-string",
            "reply_users": ["user-id-list"],
            "parent_user_id": "parent-user-id",
            "blocks": [...] // Rich text formatting
        }
    ]
}
```

**KEY FIELDS TO ANALYZE:**

1. **timestamp (ts)**: Use to understand chronological order and recency of messages
2. **channel.id & channel.name**: Understand the context/team where discussion is happening  
3. **user & username**: Track who is responsible for what and who is being asked to do things
4. **text**: The actual message content to analyze for problems and action items
5. **thread_ts**: Identifies threaded conversations and replies
6. **reply_count**: Indicates level of engagement and ongoing discussion
7. **parent_user_id**: Shows who initiated a thread that others are replying to
8. **reply_users**: List of people engaged in the thread
9. **channel.is_private/is_im**: Understand if this is a private discussion vs public channel

**ANALYSIS PRIORITIES:**

1. **ACTION ITEM DETECTION** (MOST IMPORTANT):
   - Look for explicit requests, assignments, or commitments that are relevant to the current user
   - Identify if someone was asked to do something and hasn't confirmed completion
   - Check if there are follow-up questions that need answers
   - Determine if the target message creates any pending obligations

2. **PROBLEM SUMMARY**:
   - Identify the core issue or topic being discussed
   - Understand the context from previous messages
   - Summarize what problem needs to be solved or what decision needs to be made

**OUTPUT FORMAT:**

Respond with ONLY a JSON object in this exact format:

```json
{
    "has_pending_action_items": true/false,
    "action_items": [
        {
            "description": "Clear description of what needs to be done",
            "responsible_user": "user-id or username if identifiable",
            "urgency": "high/medium/low",
            "context": "Brief context of why this action is needed"
        }
    ],
    "problem_summary": "Concise summary of the main problem or topic being discussed in this thread",
    "conversation_status": "active/resolved/pending_response",
    "key_participants": ["list-of-main-participants"],
    "last_activity_timestamp": "most-recent-timestamp-in-conversation"
}
```

**ANALYSIS GUIDELINES:**
 
- Focus on the target message as the primary context
- Use previous messages to understand background
- Use next messages and replies to see if issues were resolved
- Pay special attention to questions, requests, and commitments
- If someone says "I'll do X" or "Let me check Y", that's likely an action item
- If someone asks "Can you do Z?" and there's no clear resolution, that's a pending action item
- Consider the recency of messages - older conversations may be less urgent
- Look for patterns like "any updates on this?" which indicate pending items"""
                },
                {
                    "role": "user", 
                    "content": f"Please analyze the following Slack conversation context and determine if there are pending action items and summarize the problem being discussed:\n\n{conversation_context}"
                }
            ]
        )
        
        return response
    
    def _format_conversation_context(
        self,
        target_message: Dict[str, Any],
        previous_messages: List[Dict[str, Any]] = None,
        next_messages: List[Dict[str, Any]] = None,
        replies: List[Dict[str, Any]] = None
    ) -> str:
        """
        Format the conversation context into a structured JSON for the LLM.
        """
        context = {
            "target_message": target_message,
            "previous_messages": previous_messages or [],
            "next_messages": next_messages or [],
            "replies": replies or []
        }
        
        return json.dumps(context, indent=2)


# Convenience function for direct usage
def analyze_slack_conversation(
    target_message: Dict[str, Any],
    previous_messages: List[Dict[str, Any]] = None,
    next_messages: List[Dict[str, Any]] = None,
    replies: List[Dict[str, Any]] = None
) -> str:
    """
    Convenience function to analyze a Slack conversation context.
    
    Args:
        target_message (Dict): The main message that the user was mentioned in
        previous_messages (List[Dict]): Previous messages for context
        next_messages (List[Dict]): Next messages for context  
        replies (List[Dict]): All replies to the target message
        
    Returns:
        str: The LLM analysis result in JSON format
    """
    analyzer = SlackConversationAnalyzer()
    return analyzer.analyze_conversation_context(target_message, previous_messages, next_messages, replies)
