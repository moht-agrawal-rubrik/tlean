"""
LLM-based analyzer for Slack message contexts.

This module integrates with the LLM to analyze Slack message contexts and
generate structured summaries with action items, similar to GitHub format.
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from openai import OpenAI

from .slack import MessageContext, SlackMessage

# Import common models
try:
    from common.models import AnalyzedItem, slack_result_to_analyzed_item
except ImportError:
    # Fallback for different import paths
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from common.models import AnalyzedItem, slack_result_to_analyzed_item

# Import SlackConversationAnalyzer with proper error handling
try:
    from llm_interactions.generateConversationSummarySlack import SlackConversationAnalyzer
except ImportError:
    # Fallback for different import paths
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from llm_interactions.generateConversationSummarySlack import SlackConversationAnalyzer

# Configure logger for this module
logger = logging.getLogger(__name__)

# Set up detailed logging for LLM interactions
# You can control this via environment variable: LLM_LOG_LEVEL=DEBUG
llm_log_level = os.getenv('LLM_LOG_LEVEL', 'INFO').upper()
if llm_log_level == 'DEBUG':
    logger.setLevel(logging.DEBUG)
elif llm_log_level == 'TRACE':
    logger.setLevel(5)  # Custom TRACE level for very detailed logging


class SlackMessageAnalyzer:
    """
    LLM-based analyzer for Slack message contexts.

    This class processes MessageContext objects through an LLM to generate
    structured analysis including action items, summaries, and scores.
    """

    def __init__(self):
        """Initialize the analyzer with the updated SlackConversationAnalyzer."""
        self.conversation_analyzer = SlackConversationAnalyzer()
    
    def analyze_message_context(self, context: MessageContext, target_user_id: str) -> AnalyzedItem:
        """
        Analyze a MessageContext using LLM to generate structured insights.

        Args:
            context: MessageContext object to analyze
            target_user_id: The user ID this analysis is for

        Returns:
            AnalyzedItem with common format for all integrations
        """
        message_ts = context.original_message.ts
        message_preview = context.original_message.text[:100] + "..." if len(context.original_message.text) > 100 else context.original_message.text

        logger.info(f"🧠 Starting LLM analysis for message {message_ts}")
        logger.debug(f"   📝 Message preview: {message_preview}")
        logger.debug(f"   👤 Target user: {target_user_id}")
        logger.debug(f"   📊 Context: {len(context.previous_messages)} prev, {len(context.next_messages)} next, {len(context.replies)} replies")

        try:
            # Use the updated SlackConversationAnalyzer
            logger.debug("🔄 Using SlackConversationAnalyzer for LLM analysis...")
            logger.debug(f"   📝 Message: {message_preview}")
            logger.debug(f"   👤 Target user: {target_user_id}")
            logger.debug(f"   📊 Context: {len(context.previous_messages)} prev, {len(context.next_messages)} next, {len(context.replies)} replies")

            # Get LLM analysis using the updated analyzer
            response_content = self.conversation_analyzer.analyze_conversation_context(
                message_context=context,
                target_user_id=target_user_id
            )

            # Parse LLM response
            logger.debug("🔍 Parsing LLM response...")
            llm_result = self._parse_llm_response(response_content)

            # Log parsed results
            score = llm_result.get("score", 0.0)
            action_items_count = len(llm_result.get("action_items", []))

            logger.info(f"✅ LLM analysis complete for message {message_ts}")
            logger.info(f"   📊 Score: {score}")
            logger.info(f"   ✅ Action items: {action_items_count}")

            if score > 0.6:
                logger.info(f"🚨 HIGH ATTENTION message detected: {message_preview}")
            elif score > 0.3:
                logger.info(f"⚠️  MEDIUM ATTENTION message: {message_preview}")
            else:
                logger.info(f"ℹ️  LOW/NO ATTENTION message: {message_preview}")

            # Convert to common AnalyzedItem format
            logger.debug("🔄 Converting to common AnalyzedItem format...")
            result = slack_result_to_analyzed_item(llm_result)

            logger.debug(f"✅ Analysis pipeline complete for message {message_ts}")
            return result

        except Exception as e:
            logger.error(f"❌ Error analyzing message context {message_ts}: {e}")
            logger.error(f"   📝 Message: {message_preview}")
            logger.error(f"   👤 Target user: {target_user_id}")
            logger.exception("Full error traceback:")

            # Return a fallback structure
            logger.warning(f"🔄 Using fallback analysis for message {message_ts}")
            fallback_dict = self._create_fallback_analysis(context, target_user_id)
            return slack_result_to_analyzed_item(fallback_dict)
    

    
    def _parse_llm_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse LLM response text into structured data.

        Args:
            response_text: Raw response from LLM

        Returns:
            Parsed dictionary or fallback structure
        """
        logger.debug("🔍 Parsing LLM response...")

        try:
            # Try to extract JSON from the response
            original_text = response_text
            response_text = response_text.strip()

            logger.debug(f"   📏 Response length: {len(response_text)} characters")

            # Find JSON block if wrapped in markdown
            if "```json" in response_text:
                logger.debug("   🔍 Found JSON markdown block")
                start = response_text.find("```json") + 7
                end = response_text.find("```", start)
                response_text = response_text[start:end].strip()
                logger.debug(f"   ✂️  Extracted JSON block: {len(response_text)} characters")
            elif "```" in response_text:
                logger.debug("   🔍 Found generic markdown block")
                start = response_text.find("```") + 3
                end = response_text.find("```", start)
                response_text = response_text[start:end].strip()
                logger.debug(f"   ✂️  Extracted generic block: {len(response_text)} characters")

            logger.debug("   🔄 Attempting JSON parse...")
            parsed_result = json.loads(response_text)

            # Validate required fields
            required_fields = ["source", "title", "score", "conversation_status"]
            missing_fields = [field for field in required_fields if field not in parsed_result]

            if missing_fields:
                logger.warning(f"   ⚠️  Missing required fields in LLM response: {missing_fields}")
            else:
                logger.debug("   ✅ JSON parsing successful, all required fields present")

            # Log key parsed values
            score = parsed_result.get("score", "N/A")
            status = parsed_result.get("conversation_status", "N/A")
            action_count = len(parsed_result.get("action_items", []))
            logger.debug(f"   📊 Parsed - Score: {score}, Status: {status}, Actions: {action_count}")

            return parsed_result

        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"❌ Failed to parse LLM response as JSON: {e}")
            logger.warning(f"   📝 Response preview: {response_text[:200]}...")

            # Log the full response for debugging if it's not too long
            if len(original_text) < 2000:
                logger.debug(f"   📋 Full response that failed to parse:\n{original_text}")
            else:
                logger.debug(f"   📋 Response too long to log ({len(original_text)} chars)")

            # Return a basic fallback structure
            logger.warning("   🔄 Using fallback parsing structure")
            return {
                "source": "slack",
                "title": "Slack Conversation",
                "long_summary": "Unable to parse LLM analysis - response format error",
                "action_items": ["Review conversation manually - LLM parsing failed"],
                "score": 0.5,
                "urgency": "medium",
                "conversation_status": "needs_review"
            }
    
    def _convert_to_structured_format(
        self, 
        context: MessageContext, 
        llm_result: Dict[str, Any],
        target_user_id: str
    ) -> Dict[str, Any]:
        """
        Convert LLM result to our final structured format.
        
        Args:
            context: Original MessageContext
            llm_result: Parsed LLM response
            target_user_id: Target user ID
            
        Returns:
            Final structured analysis
        """
        # Ensure required fields exist with defaults
        result = {
            "source": "slack",
            "link": context.original_message.permalink or f"slack://channel/{context.original_message.channel_id}/message/{context.original_message.ts}",
            "timestamp": self._format_timestamp(context.original_message.ts),
            "title": llm_result.get("title", f"Slack message in {context.original_message.channel_name or 'DM'}"),
            "long_summary": llm_result.get("long_summary", "Slack conversation analysis"),
            "action_items": llm_result.get("action_items", []),
            "score": float(llm_result.get("score", 0.5)),
            "urgency": llm_result.get("urgency", "medium"),
            "conversation_status": llm_result.get("conversation_status", "needs_review"),
            "key_participants": llm_result.get("key_participants", []),
            "channel_context": llm_result.get("channel_context", context.original_message.channel_name or "Unknown"),
            "message_count": {
                "previous": len(context.previous_messages),
                "next": len(context.next_messages), 
                "replies": len(context.replies)
            }
        }
        
        return result
    
    def _format_timestamp(self, slack_ts: str) -> str:
        """
        Format Slack timestamp to ISO format.
        
        Args:
            slack_ts: Slack timestamp string
            
        Returns:
            ISO formatted timestamp string
        """
        try:
            dt = datetime.fromtimestamp(float(slack_ts))
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except (ValueError, TypeError):
            return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def _create_fallback_analysis(self, context: MessageContext, target_user_id: str) -> Dict[str, Any]:
        """
        Create a fallback analysis when LLM analysis fails.
        
        Args:
            context: MessageContext to analyze
            target_user_id: Target user ID
            
        Returns:
            Basic fallback analysis structure
        """
        return {
            "source": "slack",
            "link": context.original_message.permalink or f"slack://channel/{context.original_message.channel_id}",
            "timestamp": self._format_timestamp(context.original_message.ts),
            "title": f"Slack message in {context.original_message.channel_name or 'DM'}",
            "long_summary": f"Message from {context.original_message.user}: {context.original_message.text[:200]}...",
            "action_items": ["Review this conversation manually"],
            "score": 0.5,
            "urgency": "medium",
            "conversation_status": "needs_review",
            "key_participants": [context.original_message.user],
            "channel_context": context.original_message.channel_name or "Unknown",
            "message_count": {
                "previous": len(context.previous_messages),
                "next": len(context.next_messages),
                "replies": len(context.replies)
            }
        }


def analyze_message_contexts(
    contexts: List[MessageContext],
    target_user_id: str
) -> List[AnalyzedItem]:
    """
    Convenience function to analyze multiple message contexts.

    Args:
        contexts: List of MessageContext objects to analyze
        target_user_id: Target user ID for analysis

    Returns:
        List of AnalyzedItem objects in common format
    """
    logger.info(f"🚀 Starting batch LLM analysis for {len(contexts)} messages")
    logger.info(f"   👤 Target user: {target_user_id}")

    analyzer = SlackMessageAnalyzer()
    results = []
    successful_analyses = 0
    failed_analyses = 0
    total_tokens_used = 0

    for i, context in enumerate(contexts, 1):
        message_ts = context.original_message.ts
        logger.debug(f"📊 Processing message {i}/{len(contexts)} (ts: {message_ts})")

        try:
            result = analyzer.analyze_message_context(context, target_user_id)
            results.append(result)
            successful_analyses += 1

            # Track token usage if available (would need to modify analyzer to return this)
            logger.debug(f"✅ Message {i}/{len(contexts)} analyzed successfully")

        except Exception as e:
            logger.error(f"❌ Failed to analyze context {i}/{len(contexts)} for message {message_ts}: {e}")
            failed_analyses += 1

            # Add fallback result
            logger.warning(f"🔄 Using fallback analysis for message {i}/{len(contexts)}")
            fallback_dict = analyzer._create_fallback_analysis(context, target_user_id)
            fallback_item = slack_result_to_analyzed_item(fallback_dict)
            results.append(fallback_item)

    # Log batch summary
    logger.info(f"🎯 Batch LLM analysis complete!")
    logger.info(f"   ✅ Successful: {successful_analyses}/{len(contexts)}")
    logger.info(f"   ❌ Failed: {failed_analyses}/{len(contexts)}")
    logger.info(f"   📊 Success rate: {(successful_analyses/len(contexts)*100):.1f}%")

    # Analyze results distribution
    high_attention = sum(1 for r in results if r.score > 0.6)
    medium_attention = sum(1 for r in results if 0.3 < r.score <= 0.6)
    low_attention = sum(1 for r in results if r.score <= 0.3)

    logger.debug(f"   🚨 High attention (>0.6): {high_attention}")
    logger.debug(f"   ⚠️  Medium attention (0.3-0.6): {medium_attention}")
    logger.debug(f"   ℹ️  Low attention (≤0.3): {low_attention}")

    return results
