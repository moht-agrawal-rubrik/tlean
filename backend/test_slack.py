#!/usr/bin/env python3
"""
Test script for Slack API integration.

This script tests the core functionality of the Slack API integration
including OAuth token validation, user ID retrieval, and mention detection.
"""

import os
import sys
from dotenv import load_dotenv
from slack.slack import SlackAPI
from slack_sdk.errors import SlackApiError

# Load environment variables
load_dotenv()

def test_slack_integration():
    """Test the Slack API integration functionality."""
    
    print("🚀 Testing Slack API Integration")
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
        
        # Test 1: Get user ID and info
        print("\n1️⃣ Testing user authentication...")
        user_id = slack.get_user_id()
        user_info = slack.get_user_info()
        
        print(f"✅ User ID: {user_id}")
        print(f"✅ Team: {user_info.get('team', 'N/A')}")
        print(f"✅ User: {user_info.get('user', 'N/A')}")
        
        # Test 2: Get channels
        print("\n2️⃣ Testing channel access...")
        channels = slack.get_channels()
        print(f"✅ Found {len(channels)} channels user is member of")
        
        if channels:
            print("   Sample channels:")
            for channel in channels[:3]:  # Show first 3 channels
                print(f"   - #{channel.get('name', 'unknown')} ({channel.get('id', 'no-id')})")
        
        # Test 3: Get direct messages
        print("\n3️⃣ Testing direct message access...")
        dms = slack.get_direct_messages()
        print(f"✅ Found {len(dms)} direct message conversations")
        
        # Test 4: Search for mentions
        print("\n4️⃣ Testing mention search...")
        mentions = slack.search_mentions(days_back=7)
        print(f"✅ Found {len(mentions)} mentions in the last 7 days")
        
        if mentions:
            print("   Recent mentions:")
            for mention in mentions[:2]:  # Show first 2 mentions
                channel_name = mention.get('channel', {}).get('name', 'unknown')
                text_preview = mention.get('text', '')[:100] + '...' if len(mention.get('text', '')) > 100 else mention.get('text', '')
                print(f"   - #{channel_name}: {text_preview}")
        
        # Test 5: Get unreplied mentions
        print("\n5️⃣ Testing unreplied mention detection...")
        unreplied = slack.get_unreplied_mentions(days_back=7)
        print(f"✅ Found {len(unreplied)} unreplied mentions")
        
        if unreplied:
            print("   Unreplied mentions:")
            for mention in unreplied[:2]:  # Show first 2 unreplied
                channel_name = mention.get('channel', {}).get('name', 'unknown')
                days_old = mention.get('days_old', 0)
                text_preview = mention.get('text', '')[:80] + '...' if len(mention.get('text', '')) > 80 else mention.get('text', '')
                print(f"   - #{channel_name} ({days_old} days old): {text_preview}")
        
        # Test 6: Get comprehensive task list
        print("\n6️⃣ Testing comprehensive task detection...")
        tasks = slack.get_tasks_needing_attention(days_back=7)
        
        summary = tasks.get('summary', {})
        print(f"✅ Task Summary:")
        print(f"   - Total unreplied: {summary.get('total_unreplied', 0)}")
        print(f"   - Urgent (2+ days): {summary.get('urgent_count', 0)}")
        print(f"   - Recent (<2 days): {summary.get('recent_count', 0)}")
        
        print("\n🎉 All tests completed successfully!")
        print("\n📊 Summary:")
        print(f"   - User authenticated: {user_id}")
        print(f"   - Channels accessible: {len(channels)}")
        print(f"   - DM conversations: {len(dms)}")
        print(f"   - Total mentions found: {len(mentions)}")
        print(f"   - Unreplied mentions: {len(unreplied)}")
        
        return True
        
    except SlackApiError as e:
        print(f"❌ Slack API Error: {e}")
        print("This might be due to:")
        print("- Invalid or expired OAuth token")
        print("- Insufficient permissions/scopes")
        print("- Network connectivity issues")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        return False

def main():
    """Main function to run the test."""
    success = test_slack_integration()
    
    if success:
        print("\n✨ Integration test passed! Your Slack API is ready to use.")
        sys.exit(0)
    else:
        print("\n💥 Integration test failed. Please check your configuration.")
        sys.exit(1)

if __name__ == "__main__":
    main()
