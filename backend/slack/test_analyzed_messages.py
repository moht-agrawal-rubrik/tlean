#!/usr/bin/env python3
"""
Test script for the analyzed Slack messages API.

This script demonstrates the complete workflow:
1. Fetch messages with context
2. Filter messages that need attention
3. Analyze through LLM
4. Return GitHub-style structured response
"""

import os
import json
import sys
import requests
from datetime import datetime
from dotenv import load_dotenv

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from slack.slack import SlackAPI
from slack.llm_analyzer import analyze_message_contexts

# Load environment variables
load_dotenv()


def test_analyzed_messages_workflow():
    """Test the complete analyzed messages workflow."""
    
    print("🚀 Testing Analyzed Slack Messages Workflow")
    print("=" * 60)
    
    # Check if required environment variables are available
    slack_token = os.getenv('SLACK_OAUTH_TOKEN')
    openai_key = os.getenv('OPENAI_API_KEY')
    
    if not slack_token:
        print("❌ SLACK_OAUTH_TOKEN not found in environment variables")
        return False
    
    if not openai_key:
        print("❌ OPENAI_API_KEY not found in environment variables")
        return False
    
    try:
        # Initialize Slack API
        print("📡 Initializing Slack API client...")
        slack = SlackAPI()
        print("✅ Slack API initialized successfully")
        
        # Test with a sample username (change this to a username in your workspace)
        username = "satya.prakash"
        target_user_id = f"@{username}"  # In real implementation, resolve to actual user ID
        
        print(f"\n🔍 Step 1: Fetching messages with context for @{username}...")
        
        # Get messages with context
        message_contexts = slack.get_user_messages_with_context(
            username=username,
            context_limit=5,
            search_limit=10
        )
        
        print(f"✅ Found {len(message_contexts)} messages with context")
        
        if not message_contexts:
            print("No messages found. Try with a different username.")
            return True
        
        print(f"\n🔍 Step 2: Analyzing ALL messages through LLM (LLM will decide what needs attention)...")

        # Analyze ALL messages through LLM - let LLM decide what needs attention
        analyzed_results = analyze_message_contexts(
            contexts=message_contexts,
            target_user_id=target_user_id
        )

        print(f"✅ LLM analyzed {len(analyzed_results)} messages")

        # Filter based on LLM analysis
        messages_needing_attention = []
        for result in analyzed_results:
            conversation_status = result.get("conversation_status", "needs_review")
            score = result.get("score", 0.0)

            # Only include messages that LLM determined need attention
            if (conversation_status in ["needs_response", "needs_review"] and score > 0.3) or score > 0.6:
                messages_needing_attention.append(result)

        print(f"✅ LLM determined {len(messages_needing_attention)} out of {len(analyzed_results)} messages need attention")

        if not messages_needing_attention:
            print("✨ Great! LLM determined no messages need attention - all are resolved or responded to.")
            return True
        
        print(f"✅ Analyzed {len(analyzed_results)} messages through LLM")
        
        # Display results
        print(f"\n📊 Analysis Results (Messages Needing Attention):")
        print("=" * 40)

        for i, result in enumerate(messages_needing_attention, 1):
            print(f"\n📝 Message {i}:")
            print(f"   🔗 Link: {result.get('link', 'N/A')}")
            print(f"   📅 Timestamp: {result.get('timestamp', 'N/A')}")
            print(f"   📋 Title: {result.get('title', 'N/A')}")
            print(f"   📊 Score: {result.get('score', 0):.2f}")
            print(f"   🚨 Urgency: {result.get('urgency', 'N/A')}")
            print(f"   📍 Status: {result.get('conversation_status', 'N/A')}")
            print(f"   💬 Channel: {result.get('channel_context', 'N/A')}")
            
            summary = result.get('long_summary', '')
            if len(summary) > 150:
                summary = summary[:150] + "..."
            print(f"   📄 Summary: {summary}")
            
            action_items = result.get('action_items', [])
            if action_items:
                print(f"   ✅ Action Items ({len(action_items)}):")
                for j, item in enumerate(action_items[:3], 1):  # Show first 3
                    print(f"      {j}. {item}")
                if len(action_items) > 3:
                    print(f"      ... and {len(action_items) - 3} more")
            else:
                print(f"   ✅ Action Items: None")
        
        # Save detailed results
        output_file = f"analyzed_messages_{username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w') as f:
            json.dump({
                "all_analyzed": analyzed_results,
                "needing_attention": messages_needing_attention
            }, f, indent=2, default=str)

        print(f"\n💾 Detailed results saved to: {output_file}")

        # Display summary statistics
        total_action_items = sum(len(result.get('action_items', [])) for result in messages_needing_attention)
        avg_score = sum(result.get('score', 0) for result in messages_needing_attention) / len(messages_needing_attention) if messages_needing_attention else 0
        high_urgency = sum(1 for result in messages_needing_attention if result.get('urgency') == 'high')

        print(f"\n📈 Summary Statistics:")
        print(f"   🔍 Total messages analyzed by LLM: {len(analyzed_results)}")
        print(f"   🎯 Messages needing attention: {len(messages_needing_attention)}")
        print(f"   ✅ Total action items: {total_action_items}")
        print(f"   📊 Average attention score: {avg_score:.2f}")
        print(f"   🚨 High urgency messages: {high_urgency}")
        print(f"   📉 Messages filtered out: {len(analyzed_results) - len(messages_needing_attention)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in workflow test: {e}")
        return False


def test_api_endpoint():
    """Test the API endpoint directly."""
    
    print(f"\n🌐 Testing API Endpoint")
    print("=" * 30)
    
    # Test the API endpoint (assuming server is running)
    base_url = "http://localhost:8000"
    username = "satya.prakash"
    
    try:
        # Test health endpoint first
        print("🏥 Testing health endpoint...")
        health_response = requests.get(f"{base_url}/slack/health", timeout=10)
        
        if health_response.status_code == 200:
            print("✅ Health endpoint working")
        else:
            print(f"⚠️  Health endpoint returned {health_response.status_code}")
        
        # Test analyzed messages endpoint
        print(f"🔍 Testing analyzed messages endpoint for {username}...")
        
        params = {
            "context_limit": 5,
            "search_limit": 10,
            "max_age_days": 30
        }
        
        response = requests.get(
            f"{base_url}/slack/user/{username}/analyzed-messages",
            params=params,
            timeout=60  # Longer timeout for LLM processing
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ API endpoint working successfully")
            print(f"   📊 Total messages found: {data.get('total_messages_found', 0)}")
            print(f"   🎯 Messages needing attention: {data.get('messages_needing_attention', 0)}")
            print(f"   📝 Analyzed messages: {len(data.get('analyzed_messages', []))}")
            
            # Save API response
            api_output_file = f"api_response_{username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(api_output_file, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"   💾 API response saved to: {api_output_file}")
            
        else:
            print(f"❌ API endpoint failed with status {response.status_code}")
            print(f"   Response: {response.text}")
        
        return True
        
    except requests.ConnectionError:
        print("❌ Could not connect to API server")
        print("   Make sure the server is running: uvicorn main:app --reload")
        return False
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False


def main():
    """Main test function."""
    
    print("🎯 Analyzed Slack Messages Test Suite")
    print("=" * 70)
    
    # Test 1: Complete workflow
    print("\n🧪 Test 1: Complete Workflow")
    success1 = test_analyzed_messages_workflow()
    
    # Test 2: API endpoint
    print("\n🧪 Test 2: API Endpoint")
    success2 = test_api_endpoint()
    
    print("\n" + "=" * 70)
    if success1:
        print("🎉 Workflow test passed!")
        print("\n📚 Next steps:")
        print("   1. Start the FastAPI server: uvicorn main:app --reload")
        print("   2. Test the new endpoint:")
        print("      curl 'http://localhost:8000/slack/user/satya.prakash/analyzed-messages'")
        print("   3. Check the API documentation at: http://localhost:8000/docs")
        print("\n🔗 New Endpoint Features:")
        print("   ✅ Fetches messages with full context")
        print("   ✅ Filters out resolved/responded messages")
        print("   ✅ LLM analysis for action items and summaries")
        print("   ✅ GitHub-style structured response format")
        print("   ✅ Attention scoring and urgency assessment")
    else:
        print("💥 Some tests failed. Please check your configuration.")
        print("   - Verify SLACK_OAUTH_TOKEN and OPENAI_API_KEY are set")
        print("   - Ensure tokens have required permissions")
        print("   - Check that the username exists in your workspace")


if __name__ == "__main__":
    main()
