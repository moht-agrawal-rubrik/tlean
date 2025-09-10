#!/usr/bin/env python3
"""
Example demonstrating the exact curl workflow implementation.

This script shows how the SlackAPI class implements the exact same workflow
as described in the curl commands, step by step.
"""

import os
import json
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def demonstrate_curl_workflow():
    """
    Demonstrate the exact curl workflow implementation.
    
    This shows how our SlackAPI class implements the same steps as the curl commands:
    
    1st step: curl "https://slack.com/api/search.messages?query=@satya.prakash&sort=timestamp"
    2nd step: For each message, get context and replies
    """
    
    token = os.getenv('SLACK_OAUTH_TOKEN')
    if not token:
        print("❌ SLACK_OAUTH_TOKEN not found")
        return
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    base_url = "https://slack.com/api"
    username = "satya.prakash"  # Change this to your target username
    
    print("🔄 Demonstrating Curl Workflow Implementation")
    print("=" * 60)
    
    # STEP 1: Search for messages (equivalent to first curl command)
    print(f"\n📍 STEP 1: Search for messages mentioning @{username}")
    print("Equivalent curl command:")
    print(f'curl "https://slack.com/api/search.messages?query=@{username}&sort=timestamp" \\')
    print(f'-H "Authorization: Bearer {token[:10]}..."')
    
    search_params = {
        "query": f"@{username}",
        "sort": "timestamp",
        "count": 20
    }
    
    try:
        response = requests.get(
            f"{base_url}/search.messages",
            headers=headers,
            params=search_params,
            timeout=30
        )
        response.raise_for_status()
        search_data = response.json()
        
        if not search_data.get('ok'):
            print(f"❌ Search failed: {search_data.get('error')}")
            return
        
        messages = search_data.get('messages', {}).get('matches', [])
        print(f"✅ Found {len(messages)} messages")
        
        if not messages:
            print("No messages found. Try with a different username.")
            return
        
        # Process each message (STEP 2)
        for i, message in enumerate(messages[:3]):  # Process first 3 messages
            print(f"\n📍 STEP 2.{i+1}: Processing message {i+1}")
            
            channel_id = message.get('channel', {}).get('id')
            message_ts = message.get('ts')
            message_text = message.get('text', '')[:100] + "..."
            
            print(f"   Message: {message_text}")
            print(f"   Channel: {channel_id}")
            print(f"   Timestamp: {message_ts}")
            
            if not channel_id or not message_ts:
                print("   ⚠️  Skipping - missing channel_id or timestamp")
                continue
            
            # STEP 2a: Get previous messages (last 4 messages)
            print(f"\n   📍 STEP 2a: Get previous messages")
            print("   Equivalent curl command:")
            print(f'   curl "https://slack.com/api/conversations.history?channel={channel_id}&latest={message_ts}&limit=10&inclusive=true" \\')
            print(f'   -H "Authorization: Bearer {token[:10]}..."')
            
            prev_params = {
                "channel": channel_id,
                "latest": message_ts,
                "limit": 10,
                "inclusive": True
            }
            
            try:
                prev_response = requests.get(
                    f"{base_url}/conversations.history",
                    headers=headers,
                    params=prev_params,
                    timeout=30
                )
                prev_data = prev_response.json()
                
                if prev_data.get('ok'):
                    prev_messages = prev_data.get('messages', [])
                    print(f"   ✅ Found {len(prev_messages)} previous messages")
                else:
                    print(f"   ❌ Previous messages failed: {prev_data.get('error')}")
                    
            except Exception as e:
                print(f"   ❌ Error getting previous messages: {e}")
            
            # STEP 2b: Get next messages (next 4 messages)
            print(f"\n   📍 STEP 2b: Get next messages")
            print("   Equivalent curl command:")
            print(f'   curl "https://slack.com/api/conversations.history?channel={channel_id}&oldest={message_ts}&limit=10&inclusive=true" \\')
            print(f'   -H "Authorization: Bearer {token[:10]}..."')
            
            next_params = {
                "channel": channel_id,
                "oldest": message_ts,
                "limit": 10,
                "inclusive": True
            }
            
            try:
                next_response = requests.get(
                    f"{base_url}/conversations.history",
                    headers=headers,
                    params=next_params,
                    timeout=30
                )
                next_data = next_response.json()
                
                if next_data.get('ok'):
                    next_messages = next_data.get('messages', [])
                    print(f"   ✅ Found {len(next_messages)} next messages")
                else:
                    print(f"   ❌ Next messages failed: {next_data.get('error')}")
                    
            except Exception as e:
                print(f"   ❌ Error getting next messages: {e}")
            
            # STEP 2c: Get replies to the message
            print(f"\n   📍 STEP 2c: Get replies to message")
            print("   Equivalent curl command:")
            print(f'   curl "https://slack.com/api/conversations.replies?channel={channel_id}&ts={message_ts}" \\')
            print(f'   -H "Authorization: Bearer {token[:10]}..."')
            
            replies_params = {
                "channel": channel_id,
                "ts": message_ts
            }
            
            try:
                replies_response = requests.get(
                    f"{base_url}/conversations.replies",
                    headers=headers,
                    params=replies_params,
                    timeout=30
                )
                replies_data = replies_response.json()
                
                if replies_data.get('ok'):
                    all_messages = replies_data.get('messages', [])
                    replies = all_messages[1:] if len(all_messages) > 1 else []
                    print(f"   ✅ Found {len(replies)} replies")
                else:
                    print(f"   ❌ Replies failed: {replies_data.get('error')}")
                    
            except Exception as e:
                print(f"   ❌ Error getting replies: {e}")
            
            print("   " + "-" * 50)
        
        print(f"\n🎉 Workflow demonstration complete!")
        print(f"\nThis is exactly what our SlackAPI.get_user_messages_with_context() method does:")
        print(f"1. Search for messages mentioning the user")
        print(f"2. For each message:")
        print(f"   a. Get previous messages for context")
        print(f"   b. Get next messages for context") 
        print(f"   c. Get replies to the message")
        print(f"3. Structure all data into a comprehensive response")
        
        print(f"\n📚 To use the API:")
        print(f"   curl 'http://localhost:8000/slack/user/{username}/messages'")
        
    except Exception as e:
        print(f"❌ Error in workflow demonstration: {e}")


def compare_with_sample_data():
    """Compare our implementation with the provided sample JSON files."""
    
    print(f"\n🔍 Comparing with Sample Data")
    print("=" * 40)
    
    sample_files = [
        "sample_messages.json",
        "sample_previous_4_messages.json", 
        "sample_next_4_messages.json",
        "sample_replies.json"
    ]
    
    for filename in sample_files:
        filepath = os.path.join(os.path.dirname(__file__), filename)
        if os.path.exists(filepath):
            print(f"\n📄 {filename}:")
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                
                if filename == "sample_messages.json":
                    matches = data.get('messages', {}).get('matches', [])
                    print(f"   📊 Contains {len(matches)} message matches")
                    if matches:
                        print(f"   📝 First message: {matches[0].get('text', '')[:50]}...")
                        
                elif filename.startswith("sample_"):
                    messages = data.get('messages', [])
                    print(f"   📊 Contains {len(messages)} messages")
                    if messages:
                        print(f"   📝 First message: {messages[0].get('text', '')[:50]}...")
                        
            except Exception as e:
                print(f"   ❌ Error reading {filename}: {e}")
        else:
            print(f"   ⚠️  {filename} not found")


if __name__ == "__main__":
    demonstrate_curl_workflow()
    compare_with_sample_data()
