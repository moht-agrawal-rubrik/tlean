#!/usr/bin/env python3
"""
Test script for the Slack Message Retrieval API.

This script demonstrates how to use the SlackAPI class and tests
the complete workflow for fetching messages with context and replies.
"""

import os
import json
import sys
from datetime import datetime
from dotenv import load_dotenv

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from slack.slack import SlackAPI
from slack.models import message_context_to_model
from slack.exceptions import SlackAPIError

# Load environment variables
load_dotenv()


def test_slack_api():
    """Test the Slack API functionality."""
    
    print("🚀 Testing Slack Message Retrieval API")
    print("=" * 50)
    
    # Check if token is available
    token = os.getenv('SLACK_OAUTH_TOKEN')
    if not token:
        print("❌ SLACK_OAUTH_TOKEN not found in environment variables")
        print("Please set your Slack OAuth token in the .env file")
        return False
    
    try:
        # Initialize Slack API
        print("📡 Initializing Slack API client...")
        slack = SlackAPI()
        print("✅ Slack API initialized successfully")
        
        # Test with a sample username (you can change this)
        username = "satya.prakash"  # Change this to a username in your Slack workspace
        
        print(f"\n🔍 Searching for messages mentioning @{username}...")
        
        # Test the complete workflow
        message_contexts = slack.get_user_messages_with_context(
            username=username,
            context_limit=5,  # Get 5 previous/next messages for context
            search_limit=10   # Search for up to 10 messages
        )
        
        print(f"✅ Found {len(message_contexts)} messages with context")
        
        if message_contexts:
            print("\n📋 Message Summary:")
            for i, context in enumerate(message_contexts, 1):
                print(f"\n  Message {i}:")
                print(f"    📝 Original: {context.original_message.text[:100]}...")
                print(f"    📅 Timestamp: {context.original_message.ts}")
                print(f"    📍 Channel: {context.original_message.channel_name or context.original_message.channel_id}")
                print(f"    ⬅️  Previous messages: {len(context.previous_messages)}")
                print(f"    ➡️  Next messages: {len(context.next_messages)}")
                print(f"    💬 Replies: {len(context.replies)}")
                
                if context.replies:
                    print("    Reply preview:")
                    for reply in context.replies[:2]:  # Show first 2 replies
                        print(f"      💬 {reply.text[:80]}...")
        
        # Test converting to Pydantic models
        print(f"\n🔄 Converting to API response format...")
        context_models = [message_context_to_model(ctx) for ctx in message_contexts]
        
        # Create a sample API response structure
        api_response = {
            "user_id": username,
            "username": username,
            "total_messages_found": len(context_models),
            "messages_with_context": [model.model_dump() for model in context_models],
            "search_parameters": {
                "context_limit": 5,
                "search_limit": 10,
                "search_query": f"@{username}"
            },
            "timestamp": datetime.now().isoformat()
        }
        
        # Save the response to a file for inspection
        output_file = f"test_response_{username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w') as f:
            json.dump(api_response, f, indent=2, default=str)
        
        print(f"✅ API response saved to: {output_file}")
        
        # Display some statistics
        total_related = sum(
            len(ctx.previous_messages) + len(ctx.next_messages) + len(ctx.replies)
            for ctx in message_contexts
        )
        
        print(f"\n📊 Statistics:")
        print(f"   🎯 Main messages found: {len(message_contexts)}")
        print(f"   🔗 Total related messages: {total_related}")
        print(f"   📈 Average context per message: {total_related / len(message_contexts) if message_contexts else 0:.1f}")
        
        return True
        
    except SlackAPIError as e:
        print(f"❌ Slack API Error: {e}")
        print(f"   Error code: {e.error_code}")
        if e.details:
            print(f"   Details: {e.details}")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        return False


def test_individual_methods():
    """Test individual SlackAPI methods."""
    
    print("\n🧪 Testing Individual Methods")
    print("=" * 30)
    
    try:
        slack = SlackAPI()
        username = "satya.prakash"  # Change this to test with different users
        
        # Test search only
        print(f"🔍 Testing search for @{username}...")
        search_results = slack.search_user_messages(username, limit=5)
        print(f"✅ Search returned {len(search_results)} results")
        
        if search_results:
            # Test conversation history with the first result
            first_message = search_results[0]
            channel_id = first_message.get('channel', {}).get('id')
            message_ts = first_message.get('ts')
            
            if channel_id and message_ts:
                print(f"📜 Testing conversation history for channel {channel_id}...")
                
                # Test previous messages
                prev_messages = slack.get_conversation_history(
                    channel_id, message_ts, limit=3, direction="previous"
                )
                print(f"✅ Found {len(prev_messages)} previous messages")
                
                # Test next messages
                next_messages = slack.get_conversation_history(
                    channel_id, message_ts, limit=3, direction="next"
                )
                print(f"✅ Found {len(next_messages)} next messages")
                
                # Test replies
                print(f"💬 Testing replies for message {message_ts}...")
                replies = slack.get_message_replies(channel_id, message_ts)
                print(f"✅ Found {len(replies)} replies")
        
        return True
        
    except Exception as e:
        print(f"❌ Individual method test failed: {e}")
        return False


def main():
    """Main test function."""
    
    print("🎯 Slack Message Retrieval API Test Suite")
    print("=" * 60)
    
    # Test 1: Complete workflow
    success1 = test_slack_api()
    
    # Test 2: Individual methods
    success2 = test_individual_methods()
    
    print("\n" + "=" * 60)
    if success1 and success2:
        print("🎉 All tests passed! The Slack API is working correctly.")
        print("\n📚 Next steps:")
        print("   1. Start the FastAPI server: uvicorn main:app --reload")
        print("   2. Test the API endpoints:")
        print("      - GET /slack/health")
        print("      - GET /slack/user/{username}/messages")
        print("   3. Check the API documentation at: http://localhost:8000/docs")
    else:
        print("💥 Some tests failed. Please check your configuration.")
        print("   - Verify your SLACK_OAUTH_TOKEN is valid")
        print("   - Ensure your token has the required scopes")
        print("   - Check that the username exists in your workspace")


if __name__ == "__main__":
    main()
