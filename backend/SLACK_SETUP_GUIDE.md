# Slack Integration Setup Guide

This guide walks you through setting up the Slack integration to detect unreplied mentions and generate task lists.

## Overview

The Slack integration provides:
- **OAuth Token Management**: Secure authentication with Slack
- **User ID Retrieval**: Get your Slack user information
- **Mention Detection**: Find all mentions across channels and DMs
- **Reply Tracking**: Identify which mentions you haven't replied to
- **Task Prioritization**: Organize unreplied mentions by urgency

## Step 1: Create a Slack App

1. Go to [https://api.slack.com/apps](https://api.slack.com/apps)
2. Click **"Create New App"**
3. Choose **"From scratch"**
4. Enter app name (e.g., "TLean Task Tracker")
5. Select your workspace
6. Click **"Create App"**

## Step 2: Configure OAuth Scopes

1. In your app settings, go to **"OAuth & Permissions"**
2. Scroll down to **"Scopes"**
3. Under **"Bot Token Scopes"**, add these scopes:

   **Required Scopes:**
   - `channels:read` - View basic information about public channels
   - `groups:read` - View basic information about private channels  
   - `im:read` - View basic information about direct messages
   - `search:read` - Search messages and files
   - `users:read` - View people in the workspace

   **Optional (for future features):**
   - `chat:write` - Send messages as the bot
   - `files:read` - View files shared in channels

## Step 3: Install App to Workspace

1. In **"OAuth & Permissions"**, click **"Install to Workspace"**
2. Review the permissions and click **"Allow"**
3. Copy the **"Bot User OAuth Token"** (starts with `xoxb-`)

## Step 4: Configure Environment

1. In the `backend` directory, copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your OAuth token:
   ```bash
   SLACK_OAUTH_TOKEN=xoxb-your-bot-token-here
   ```

## Step 5: Test the Integration

1. Activate your virtual environment:
   ```bash
   source .venv/bin/activate  # macOS/Linux
   # or
   .venv\Scripts\activate     # Windows
   ```

2. Run the test script:
   ```bash
   python test_slack.py
   ```

3. If successful, you should see:
   ```
   🚀 Testing Slack API Integration
   ✅ User ID: U1234567890
   ✅ Found X channels user is member of
   ✅ Found X mentions in the last 7 days
   🎉 All tests completed successfully!
   ```

## Step 6: Try the Example

Run the example script to see your unreplied mentions:

```bash
python example_usage.py
```

This will show:
- Your user information
- Summary of unreplied mentions
- Urgent mentions (2+ days old)
- Recent mentions (<2 days old)
- Recommended actions

## Step 7: Start the API Server

1. Start the FastAPI server:
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

2. Test the API endpoints:
   ```bash
   # Get your user info
   curl "http://localhost:8000/slack/user"
   
   # Get unreplied mentions
   curl "http://localhost:8000/slack/unreplied-mentions?days_back=7"
   
   # Get comprehensive task list
   curl "http://localhost:8000/slack/tasks"
   ```

3. View API documentation at: http://localhost:8000/docs

## Troubleshooting

### Common Issues

**❌ "Invalid token" error:**
- Verify your token starts with `xoxb-`
- Make sure you copied the Bot User OAuth Token, not the User OAuth Token
- Check that the app is installed to your workspace

**❌ "Missing scope" error:**
- Go back to OAuth & Permissions in your app settings
- Add the missing scopes listed in Step 2
- Reinstall the app to your workspace

**❌ "No mentions found" but you know there are mentions:**
- The search API may have limitations on older messages
- Try reducing `days_back` parameter
- Make sure you're mentioned with `@username` in messages

**❌ "Channel not found" errors:**
- Make sure the bot is added to private channels where you're mentioned
- For DMs, the bot needs to be in the conversation

### Getting Help

1. Check the Slack API documentation: [https://api.slack.com/web](https://api.slack.com/web)
2. Review your app's event logs in the Slack app settings
3. Enable debug logging by setting `LOG_LEVEL=DEBUG` in your `.env` file

## Security Notes

- Keep your OAuth token secure and never commit it to version control
- The `.env` file is already in `.gitignore` to prevent accidental commits
- Consider using environment-specific tokens for development vs. production
- Regularly rotate your OAuth tokens for security

## Next Steps

Once the integration is working:

1. **Integrate with Frontend**: Use the API endpoints in your React frontend
2. **Add Scheduling**: Set up periodic checks for new mentions
3. **Enhance Filtering**: Add filters for specific channels or users
4. **Add Notifications**: Get alerts for urgent unreplied mentions
5. **Expand to Other Platforms**: Add similar integrations for GitHub and Jira
