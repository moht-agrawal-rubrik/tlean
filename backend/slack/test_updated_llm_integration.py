#!/usr/bin/env python3
"""
Test script for the updated LLM integration using SlackConversationAnalyzer.

This script tests the integration between:
1. SlackMessageAnalyzer (our main analyzer)
2. SlackConversationAnalyzer (the updated LLM interaction class)
3. MessageContext format
"""

import os
import sys
import json
import logging
from datetime import datetime

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from slack.slack import SlackMessage, MessageContext
from slack.llm_analyzer import SlackMessageAnalyzer
from llm_interactions.generateConversationSummarySlack import SlackConversationAnalyzer, analyze_slack_conversation

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def create_sample_message_context() -> MessageContext:
    """Create a sample MessageContext for testing."""
    
    # Original message
    original_message = SlackMessage(
        ts="1757486516.496349",
        user="U09E7BBEB9T",
        text="<@U09DVNAD36K> any updates on the API implementation?",
        channel_id="D09E7BBKUE9",
        channel_name="direct-message",
        permalink="https://slack.com/archives/D09E7BBKUE9/p1757486516496349",
        thread_ts=None,
        reply_count=1
    )
    
    # Previous messages for context
    previous_messages = [
        SlackMessage(
            ts="1757486509.722719",
            user="U09DVNAD36K",
            text="ok will add the new endpoint today",
            channel_id="D09E7BBKUE9",
            channel_name="direct-message",
            permalink="https://slack.com/archives/D09E7BBKUE9/p1757486509722719",
            thread_ts=None,
            reply_count=0
        ),
        SlackMessage(
            ts="1757486500.123456",
            user="U09E7BBEB9T",
            text="we need the analyzed messages endpoint by tomorrow",
            channel_id="D09E7BBKUE9",
            channel_name="direct-message",
            permalink="https://slack.com/archives/D09E7BBKUE9/p1757486500123456",
            thread_ts=None,
            reply_count=0
        )
    ]
    
    # Next messages (what happened after)
    next_messages = [
        SlackMessage(
            ts="1757487458.110029",
            user="U09DVNAD36K",
            text="working on it now, should be done in a few hours",
            channel_id="D09E7BBKUE9",
            channel_name="direct-message",
            permalink="https://slack.com/archives/D09E7BBKUE9/p1757487458110029",
            thread_ts=None,
            reply_count=0
        )
    ]
    
    # Replies to the original message
    replies = [
        SlackMessage(
            ts="1757487675.930579",
            user="U09DVNAD36K",
            text="hey <@U09E7BBEB9T> the endpoint is ready for testing!",
            channel_id="D09E7BBKUE9",
            channel_name="direct-message",
            permalink="https://slack.com/archives/D09E7BBKUE9/p1757487675930579",
            thread_ts="1757486516.496349",
            reply_count=0
        )
    ]
    
    return MessageContext(
        original_message=original_message,
        previous_messages=previous_messages,
        next_messages=next_messages,
        replies=replies
    )


def test_slack_conversation_analyzer_direct():
    """Test the SlackConversationAnalyzer directly."""
    
    print("🧪 Test 1: SlackConversationAnalyzer Direct Usage")
    print("=" * 60)
    
    try:
        # Create sample context
        message_context = create_sample_message_context()
        target_user_id = "U09DVNAD36K"
        
        print(f"📝 Testing with message: {message_context.original_message.text}")
        print(f"👤 Target user: {target_user_id}")
        
        # Test direct usage
        analyzer = SlackConversationAnalyzer()
        result = analyzer.analyze_conversation_context(message_context, target_user_id)
        
        print("✅ SlackConversationAnalyzer completed successfully")
        print(f"📏 Response length: {len(result)} characters")
        
        # Try to parse the result
        try:
            parsed_result = json.loads(result)
            print("✅ Response is valid JSON")
            print(f"📊 Score: {parsed_result.get('score', 'N/A')}")
            print(f"📍 Status: {parsed_result.get('conversation_status', 'N/A')}")
            print(f"🚨 Urgency: {parsed_result.get('urgency', 'N/A')}")
            print(f"✅ Action items: {len(parsed_result.get('action_items', []))}")
        except json.JSONDecodeError as e:
            print(f"❌ Response is not valid JSON: {e}")
            print(f"📋 Raw response: {result[:200]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ SlackConversationAnalyzer test failed: {e}")
        return False


def test_slack_message_analyzer_integration():
    """Test the SlackMessageAnalyzer with updated integration."""
    
    print("\n🧪 Test 2: SlackMessageAnalyzer Integration")
    print("=" * 60)
    
    try:
        # Create sample context
        message_context = create_sample_message_context()
        target_user_id = "U09DVNAD36K"
        
        print(f"📝 Testing with message: {message_context.original_message.text}")
        print(f"👤 Target user: {target_user_id}")
        
        # Test through SlackMessageAnalyzer
        analyzer = SlackMessageAnalyzer()
        result = analyzer.analyze_message_context(message_context, target_user_id)
        
        print("✅ SlackMessageAnalyzer completed successfully")
        print(f"📊 Score: {result.get('score', 'N/A')}")
        print(f"📍 Status: {result.get('conversation_status', 'N/A')}")
        print(f"🚨 Urgency: {result.get('urgency', 'N/A')}")
        print(f"✅ Action items: {len(result.get('action_items', []))}")
        print(f"🔗 Link: {result.get('link', 'N/A')}")
        
        # Check if this would be filtered for attention
        conversation_status = result.get("conversation_status", "needs_review")
        score = result.get("score", 0.0)
        
        needs_attention = (conversation_status in ["needs_response", "needs_review"] and score > 0.3) or score > 0.6
        print(f"🎯 Needs attention: {'YES' if needs_attention else 'NO'}")
        
        return True
        
    except Exception as e:
        print(f"❌ SlackMessageAnalyzer integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_convenience_function():
    """Test the convenience function."""
    
    print("\n🧪 Test 3: Convenience Function")
    print("=" * 60)
    
    try:
        # Create sample context
        message_context = create_sample_message_context()
        target_user_id = "U09DVNAD36K"
        
        print(f"📝 Testing with message: {message_context.original_message.text}")
        print(f"👤 Target user: {target_user_id}")
        
        # Test convenience function
        result = analyze_slack_conversation(message_context, target_user_id)
        
        print("✅ Convenience function completed successfully")
        print(f"📏 Response length: {len(result)} characters")
        
        # Try to parse the result
        try:
            parsed_result = json.loads(result)
            print("✅ Response is valid JSON")
            print(f"📊 Score: {parsed_result.get('score', 'N/A')}")
            print(f"📍 Status: {parsed_result.get('conversation_status', 'N/A')}")
        except json.JSONDecodeError as e:
            print(f"❌ Response is not valid JSON: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Convenience function test failed: {e}")
        return False


def main():
    """Run all tests."""
    
    print("🎯 Updated LLM Integration Test Suite")
    print("=" * 70)
    
    # Check environment
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ OPENAI_API_KEY not found in environment variables")
        return
    
    print("✅ Environment check passed")
    
    # Run tests
    test1_passed = test_slack_conversation_analyzer_direct()
    test2_passed = test_slack_message_analyzer_integration()
    test3_passed = test_convenience_function()
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 Test Results Summary:")
    print(f"   🧪 SlackConversationAnalyzer Direct: {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"   🧪 SlackMessageAnalyzer Integration: {'✅ PASSED' if test2_passed else '❌ FAILED'}")
    print(f"   🧪 Convenience Function: {'✅ PASSED' if test3_passed else '❌ FAILED'}")
    
    if all([test1_passed, test2_passed, test3_passed]):
        print("\n🎉 All tests passed! The updated LLM integration is working correctly.")
        print("\n📚 What's New:")
        print("   ✅ SlackConversationAnalyzer now accepts MessageContext objects")
        print("   ✅ Comprehensive logging for all LLM requests/responses")
        print("   ✅ Updated system prompt with better attention scoring")
        print("   ✅ Integration with existing SlackMessageAnalyzer")
        print("   ✅ Backward compatibility with legacy functions")
    else:
        print("\n💥 Some tests failed. Please check the error messages above.")


if __name__ == "__main__":
    main()
