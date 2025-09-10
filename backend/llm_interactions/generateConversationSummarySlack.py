import os
import json
import logging
from openai import OpenAI
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

# Import our MessageContext class
try:
    from ..slack.slack import MessageContext, SlackMessage
except ImportError:
    # Fallback for direct execution
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from slack.slack import MessageContext, SlackMessage

logger = logging.getLogger(__name__)


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
        message_context: MessageContext,
        target_user_id: str
    ) -> str:
        """
        Analyze a Slack conversation with full context to determine action items and problem summary.

        Args:
            message_context (MessageContext): The complete message context with original message,
                                            previous messages, next messages, and replies
            target_user_id (str): The user ID this analysis is for

        Returns:
            str: The LLM analysis result in JSON format
        """
        logger.info(f"🧠 Analyzing conversation context for message {message_context.original_message.ts}")
        logger.debug(f"   👤 Target user: {target_user_id}")

        # Log complete message details
        logger.info("📝 COMPLETE MESSAGE CONTENT:")
        logger.info(f"   🎯 Original Message:")
        logger.info(f"      📅 Timestamp: {message_context.original_message.ts}")
        logger.info(f"      👤 User: {message_context.original_message.user}")
        logger.info(f"      💬 Text: {message_context.original_message.text}")
        logger.info(f"      📍 Channel: {message_context.original_message.channel_name} ({message_context.original_message.channel_id})")
        logger.info(f"      🔗 Permalink: {message_context.original_message.permalink}")

        logger.info(f"   ⬅️  Previous Messages ({len(message_context.previous_messages)}):")
        for i, msg in enumerate(message_context.previous_messages, 1):
            logger.info(f"      {i}. [{msg.ts}] {msg.user}: {msg.text}")

        logger.info(f"   ➡️  Next Messages ({len(message_context.next_messages)}):")
        for i, msg in enumerate(message_context.next_messages, 1):
            logger.info(f"      {i}. [{msg.ts}] {msg.user}: {msg.text}")

        logger.info(f"   💬 Replies ({len(message_context.replies)}):")
        for i, msg in enumerate(message_context.replies, 1):
            logger.info(f"      {i}. [{msg.ts}] {msg.user}: {msg.text}")

        # Format the conversation context for the LLM
        conversation_context = self._format_message_context_for_llm(
            message_context, target_user_id
        )
        
        logger.info(f"📤 Sending LLM request for message {message_context.original_message.ts}")
        logger.info(f"   📏 Input size: {len(conversation_context)} characters")

        # Log the complete LLM input
        logger.info("📋 COMPLETE LLM INPUT:")
        logger.info("=" * 80)
        logger.info("🎯 SYSTEM PROMPT:")
        system_prompt = """You are an expert Slack conversation analyzer designed to identify action items and summarize conversations for busy professionals. You will receive structured JSON data representing a Slack conversation with full context.

**INPUT DATA STRUCTURE:**

You will receive a JSON object with the following structure:

```json
{
    "target_user_id": "U09DVNAD36K",
    "original_message": {
        "ts": "1757486516.496349",
        "user": "U09E7BBEB9T",
        "text": "<@U09DVNAD36K> any updates on this?",
        "channel_id": "D09E7BBKUE9",
        "channel_name": "direct-message",
        "permalink": "https://slack.com/archives/...",
        "thread_ts": null,
        "reply_count": 1
    },
    "previous_messages": [
        {
            "ts": "1757486509.722719",
            "user": "U09DVNAD36K",
            "text": "ok will add",
            "channel_id": "D09E7BBKUE9",
            "channel_name": "direct-message",
            "permalink": "https://slack.com/archives/..."
        }
    ],
    "next_messages": [
        {
            "ts": "1757487458.110029",
            "user": "U09DVNAD36K",
            "text": "i think this done",
            "channel_id": "D09E7BBKUE9",
            "channel_name": "direct-message",
            "permalink": "https://slack.com/archives/..."
        }
    ],
    "replies": [
        {
            "ts": "1757487675.930579",
            "user": "U09DVNAD36K",
            "text": "hey <@U09E7BBEB9T> this is done.",
            "channel_id": "D09E7BBKUE9",
            "channel_name": "direct-message",
            "permalink": "https://slack.com/archives/...",
            "thread_ts": "1757486516.496349"
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

Respond with ONLY a JSON object in this exact format (common format for all integrations):

```json
{
    "source": "slack",
    "link": "permalink-from-original-message",
    "timestamp": "ISO-formatted-timestamp-of-original-message",
    "title": "Brief descriptive title of the conversation",
    "long_summary": "Detailed summary of the conversation, problems discussed, and context",
    "action_items": [
        "Specific action item 1 that needs attention",
        "Specific action item 2 that needs attention"
    ],
    "score": 0.75
}
```

**IMPORTANT**: Only include these 6 fields. Do not include urgency, conversation_status, key_participants, channel_context, or any other fields.

**SCORING GUIDELINES:**

- 0.8-1.0: Urgent action needed, explicit requests, deadlines mentioned
- 0.6-0.8: Important but not urgent, follow-up needed, questions asked
- 0.4-0.6: Moderate importance, informational with some action potential
- 0.2-0.4: Low priority, mostly informational
- 0.0-0.2: No action needed, resolved or informational only

**ANALYSIS GUIDELINES:**

- Focus on what the TARGET USER specifically needs to do
- Look for explicit requests, questions directed at the target user
- Consider the conversation flow and whether issues were resolved
- Pay attention to urgency indicators (deadlines, "urgent", "ASAP", etc.)
- Consider the channel context (DM = more urgent, public channel = less urgent)
- Look for follow-up requests like "any updates?" which indicate pending items
- Use previous messages to understand background context
- Use next messages and replies to see if issues were already resolved
- If someone asks "Can you do Z?" and there's no clear resolution, that's a pending action item"""
        logger.info(system_prompt)

        user_prompt = f"Please analyze the following Slack conversation context and determine if there are pending action items and summarize the problem being discussed. Follow the system prompt guidelines and provide the output in the exact JSON format specified:\n\n{conversation_context}"
        logger.info("\n👤 USER PROMPT:")
        logger.info(user_prompt)
        logger.info("=" * 80)

        # Create the LLM request
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert Slack conversation analyzer designed to identify action items and summarize conversations for busy professionals. You will receive structured JSON data representing a Slack conversation with full context.

**INPUT DATA STRUCTURE:**

You will receive a JSON object with the following structure:

```json
{
    "target_user_id": "U09DVNAD36K",
    "original_message": {
        "ts": "1757486516.496349",
        "user": "U09E7BBEB9T",
        "text": "<@U09DVNAD36K> any updates on this?",
        "channel_id": "D09E7BBKUE9",
        "channel_name": "direct-message",
        "permalink": "https://slack.com/archives/...",
        "thread_ts": null,
        "reply_count": 1
    },
    "previous_messages": [
        {
            "ts": "1757486509.722719",
            "user": "U09DVNAD36K",
            "text": "ok will add",
            "channel_id": "D09E7BBKUE9",
            "channel_name": "direct-message",
            "permalink": "https://slack.com/archives/..."
        }
    ],
    "next_messages": [
        {
            "ts": "1757487458.110029",
            "user": "U09DVNAD36K",
            "text": "i think this done",
            "channel_id": "D09E7BBKUE9",
            "channel_name": "direct-message",
            "permalink": "https://slack.com/archives/..."
        }
    ],
    "replies": [
        {
            "ts": "1757487675.930579",
            "user": "U09DVNAD36K",
            "text": "hey <@U09E7BBEB9T> this is done.",
            "channel_id": "D09E7BBKUE9",
            "channel_name": "direct-message",
            "permalink": "https://slack.com/archives/...",
            "thread_ts": "1757486516.496349"
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

Respond with ONLY a JSON object in this exact format (similar to GitHub format):

```json
{
    "source": "slack",
    "link": "permalink-from-original-message",
    "timestamp": "ISO-formatted-timestamp-of-original-message",
    "title": "Brief descriptive title of the conversation",
    "long_summary": "Detailed summary of the conversation, problems discussed, and context",
    "action_items": [
        "Specific action item 1 that needs attention",
        "Specific action item 2 that needs attention"
    ],
    "score": 0.75,
    "urgency": "high/medium/low",
    "conversation_status": "needs_response/informational/resolved",
    "key_participants": ["user1", "user2"],
    "channel_context": "channel name or type (DM, group, etc)"
}
```

**SCORING GUIDELINES:**

- 0.8-1.0: Urgent action needed, explicit requests, deadlines mentioned
- 0.6-0.8: Important but not urgent, follow-up needed, questions asked
- 0.4-0.6: Moderate importance, informational with some action potential
- 0.2-0.4: Low priority, mostly informational
- 0.0-0.2: No action needed, resolved or informational only

**ANALYSIS GUIDELINES:**

- Focus on what the TARGET USER specifically needs to do
- Look for explicit requests, questions directed at the target user
- Consider the conversation flow and whether issues were resolved
- Pay attention to urgency indicators (deadlines, "urgent", "ASAP", etc.)
- Consider the channel context (DM = more urgent, public channel = less urgent)
- Look for follow-up requests like "any updates?" which indicate pending items
- Use previous messages to understand background context
- Use next messages and replies to see if issues were already resolved
- If someone asks "Can you do Z?" and there's no clear resolution, that's a pending action item"""
                },
                    {
                        "role": "user",
                        "content": f"Please analyze the following Slack conversation context and determine if there are pending action items and summarize the problem being discussed. Follow the system prompt guidelines and provide the output in the exact JSON format specified:\n\n{conversation_context}"
                    }
                ]
            )

            logger.info(f"📥 Received LLM response for message {message_context.original_message.ts}")
            logger.info(f"   💰 Usage: {response.usage.prompt_tokens} prompt + {response.usage.completion_tokens} completion = {response.usage.total_tokens} total tokens")

            response_content = response.choices[0].message.content
            logger.info(f"   📏 Response size: {len(response_content)} characters")

            # Log the complete LLM response
            logger.info("📋 COMPLETE LLM RESPONSE:")
            logger.info("=" * 80)
            logger.info(response_content)
            logger.info("=" * 80)

            return response_content

        except Exception as e:
            logger.error(f"❌ Error in LLM request for message {message_context.original_message.ts}: {e}")
            logger.exception("Full error traceback:")
            raise
    
    def _format_message_context_for_llm(
        self,
        message_context: MessageContext,
        target_user_id: str
    ) -> str:
        """
        Format the MessageContext into a structured JSON for the LLM.

        Args:
            message_context: MessageContext object containing all message data
            target_user_id: The user ID this analysis is for

        Returns:
            JSON string formatted for LLM consumption
        """
        # Convert SlackMessage objects to dictionaries
        def message_to_dict(msg: SlackMessage) -> Dict[str, Any]:
            return {
                "ts": msg.ts,
                "user": msg.user,
                "text": msg.text,
                "channel_id": msg.channel_id,
                "channel_name": msg.channel_name,
                "permalink": msg.permalink,
                "thread_ts": msg.thread_ts,
                "reply_count": msg.reply_count
            }

        # Create the context structure expected by the LLM
        context = {
            "target_user_id": target_user_id,
            "original_message": message_to_dict(message_context.original_message),
            "previous_messages": [message_to_dict(msg) for msg in message_context.previous_messages],
            "next_messages": [message_to_dict(msg) for msg in message_context.next_messages],
            "replies": [message_to_dict(msg) for msg in message_context.replies]
        }

        logger.debug(f"   📊 Context: {len(context['previous_messages'])} prev, {len(context['next_messages'])} next, {len(context['replies'])} replies")

        formatted_json = json.dumps(context, indent=2)

        # Log the complete formatted JSON that will be sent to LLM
        logger.info("📋 FORMATTED JSON FOR LLM:")
        logger.info("-" * 60)
        logger.info(formatted_json)
        logger.info("-" * 60)

        return formatted_json


# Convenience function for direct usage
def analyze_slack_conversation(
    message_context: MessageContext,
    target_user_id: str
) -> str:
    """
    Convenience function to analyze a Slack conversation context.

    Args:
        message_context (MessageContext): The complete message context with original message,
                                        previous messages, next messages, and replies
        target_user_id (str): The user ID this analysis is for

    Returns:
        str: The LLM analysis result in JSON format
    """
    analyzer = SlackConversationAnalyzer()
    return analyzer.analyze_conversation_context(message_context, target_user_id)


# Legacy function for backward compatibility (deprecated)
def analyze_slack_conversation_legacy(
    target_message: Dict[str, Any],
    previous_messages: List[Dict[str, Any]] = None,
    next_messages: List[Dict[str, Any]] = None,
    replies: List[Dict[str, Any]] = None
) -> str:
    """
    Legacy convenience function - DEPRECATED. Use analyze_slack_conversation with MessageContext instead.

    Args:
        target_message (Dict): The main message that the user was mentioned in
        previous_messages (List[Dict]): Previous messages for context
        next_messages (List[Dict]): Next messages for context
        replies (List[Dict]): All replies to the target message

    Returns:
        str: The LLM analysis result in JSON format
    """
    logger.warning("⚠️  Using deprecated analyze_slack_conversation_legacy function. Please migrate to MessageContext format.")

    # Convert to MessageContext format (this is a simplified conversion)
    # In practice, you'd want to properly construct SlackMessage objects
    from slack.slack import SlackMessage, MessageContext

    def dict_to_slack_message(msg_dict: Dict[str, Any]) -> SlackMessage:
        return SlackMessage(
            ts=msg_dict.get('ts', ''),
            user=msg_dict.get('user', ''),
            text=msg_dict.get('text', ''),
            channel_id=msg_dict.get('channel_id', ''),
            channel_name=msg_dict.get('channel_name', ''),
            permalink=msg_dict.get('permalink', ''),
            thread_ts=msg_dict.get('thread_ts'),
            reply_count=msg_dict.get('reply_count', 0)
        )

    original_message = dict_to_slack_message(target_message)
    prev_messages = [dict_to_slack_message(msg) for msg in (previous_messages or [])]
    next_messages_list = [dict_to_slack_message(msg) for msg in (next_messages or [])]
    replies_list = [dict_to_slack_message(msg) for msg in (replies or [])]

    message_context = MessageContext(
        original_message=original_message,
        previous_messages=prev_messages,
        next_messages=next_messages_list,
        replies=replies_list
    )

    # Use a default target user ID
    target_user_id = target_message.get('user', '@unknown')

    analyzer = SlackConversationAnalyzer()
    return analyzer.analyze_conversation_context(message_context, target_user_id)
