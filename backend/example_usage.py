#!/usr/bin/env python3
"""
Example usage of the Slack API integration.

This script demonstrates how to use the SlackAPI class to:
1. Get OAuth token and user ID
2. Fetch unreplied mentions
3. Generate a task list for user attention
"""

import os
import json
from datetime import datetime
from dotenv import load_dotenv
from slack.slack import SlackAPI

# Load environment variables
load_dotenv()

def format_mention_summary(mention):
    """Format a mention for display."""
    channel_name = mention.get('channel', {}).get('name', 'unknown')
    user = mention.get('user', 'unknown')
    timestamp = mention.get('ts', '0')
    
    # Convert timestamp to readable date
    try:
        date = datetime.fromtimestamp(float(timestamp)).strftime('%Y-%m-%d %H:%M')
    except:
        date = 'unknown date'
    
    # Get text preview
    text = mention.get('text', '')
    text_preview = text[:100] + '...' if len(text) > 100 else text
    
    return {
        'channel': f"#{channel_name}",
        'from_user': user,
        'date': date,
        'preview': text_preview,
        'days_old': mention.get('days_old', 0),
        'permalink': mention.get('permalink', '')
    }

def main():
    """Main example function."""
    print("🔍 Slack Task Detection Example")
    print("=" * 50)
    
    # Check for OAuth token
    if not os.getenv('SLACK_OAUTH_TOKEN'):
        print("❌ Please set SLACK_OAUTH_TOKEN in your .env file")
        print("See README.md for setup instructions")
        return
    
    try:
        # Initialize Slack API
        slack = SlackAPI()
        
        # Get user information
        print("👤 Getting user information...")
        user_id = slack.get_user_id()
        user_info = slack.get_user_info()
        
        print(f"   User: {user_info.get('user', 'N/A')}")
        print(f"   Team: {user_info.get('team', 'N/A')}")
        print(f"   User ID: {user_id}")
        
        # Get comprehensive task list
        print("\n📋 Analyzing tasks needing attention...")
        tasks = slack.get_tasks_needing_attention(days_back=14)  # Look back 2 weeks
        
        summary = tasks['summary']
        print(f"\n📊 Summary (last {summary['days_searched']} days):")
        print(f"   Total unreplied mentions: {summary['total_unreplied']}")
        print(f"   Urgent (2+ days old): {summary['urgent_count']}")
        print(f"   Recent (<2 days old): {summary['recent_count']}")
        
        # Show urgent mentions
        if tasks['urgent_mentions']:
            print(f"\n🚨 URGENT - Mentions needing immediate attention:")
            for i, mention in enumerate(tasks['urgent_mentions'][:5], 1):  # Show top 5
                formatted = format_mention_summary(mention)
                print(f"   {i}. {formatted['channel']} - {formatted['days_old']} days ago")
                print(f"      From: {formatted['from_user']}")
                print(f"      Preview: {formatted['preview']}")
                if formatted['permalink']:
                    print(f"      Link: {formatted['permalink']}")
                print()
        
        # Show recent mentions
        if tasks['recent_mentions']:
            print(f"\n⏰ RECENT - New mentions to address:")
            for i, mention in enumerate(tasks['recent_mentions'][:3], 1):  # Show top 3
                formatted = format_mention_summary(mention)
                print(f"   {i}. {formatted['channel']} - {formatted['date']}")
                print(f"      From: {formatted['from_user']}")
                print(f"      Preview: {formatted['preview']}")
                if formatted['permalink']:
                    print(f"      Link: {formatted['permalink']}")
                print()
        
        # Generate action items
        print("✅ RECOMMENDED ACTIONS:")
        
        if summary['urgent_count'] > 0:
            print(f"   1. Address {summary['urgent_count']} urgent mentions (2+ days old)")
        
        if summary['recent_count'] > 0:
            print(f"   2. Review {summary['recent_count']} recent mentions")
        
        if summary['total_unreplied'] == 0:
            print("   🎉 Great job! No unreplied mentions found.")
        
        # Save detailed report to file
        report_file = f"slack_task_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(tasks, f, indent=2, default=str)
        
        print(f"\n💾 Detailed report saved to: {report_file}")
        
        # API endpoint examples
        print(f"\n🌐 API Endpoint Examples:")
        print(f"   Get user info: curl 'http://localhost:8000/slack/user'")
        print(f"   Get tasks: curl 'http://localhost:8000/slack/tasks?days_back=14'")
        print(f"   Get unreplied: curl 'http://localhost:8000/slack/unreplied-mentions'")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Make sure your Slack OAuth token is valid and has the required scopes.")

if __name__ == "__main__":
    main()
