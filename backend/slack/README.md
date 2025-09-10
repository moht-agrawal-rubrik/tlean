# Slack Message Retrieval API

A comprehensive API for retrieving Slack messages with context and replies for specific users.

## Overview

This API implements the workflow described in your curl commands:

1. **Search for messages** mentioning a specific user using `search.messages`
2. **Fetch context** by getting previous and next messages using `conversations.history`
3. **Get replies** to each message using `conversations.replies`
4. **Structure the data** into a comprehensive response with all related messages

## Features

- 🔍 **Message Search**: Find all messages mentioning a specific user
- 📝 **Context Retrieval**: Get previous and next messages for full conversation context
- 💬 **Reply Fetching**: Retrieve all replies to each message
- 🏗️ **Structured Response**: Well-organized JSON response with all related data
- ⚡ **FastAPI Integration**: RESTful API endpoints with automatic documentation
- 🛡️ **Error Handling**: Comprehensive error handling with specific exception types
- 📊 **Logging**: Detailed logging for debugging and monitoring

## API Endpoints

### 🆕 Analyzed Messages Endpoint (Recommended)

```
GET /slack/user/{username}/analyzed-messages
```

**The main endpoint that provides LLM-analyzed insights similar to GitHub format.**

This endpoint:
1. Fetches all messages mentioning the user with context
2. Filters out messages that don't need attention (already responded/resolved)
3. Processes remaining messages through LLM for analysis
4. Returns structured insights with action items and summaries

**Parameters:**
- `username` (path): The username to search for (e.g., 'satya.prakash')
- `context_limit` (query, optional): Number of previous/next messages (1-50, default: 10)
- `search_limit` (query, optional): Maximum messages to search (1-100, default: 20)
- `max_age_days` (query, optional): Maximum age of messages to consider (1-90, default: 30)

**Example:**
```bash
curl "http://localhost:8000/slack/user/satya.prakash/analyzed-messages?context_limit=10&search_limit=20&max_age_days=30"
```

### Raw Messages Endpoint

```
GET /slack/user/{username}/messages
```

Retrieves all messages mentioning a user with full context and replies (without filtering or LLM analysis).

**Parameters:**
- `username` (path): The username to search for (e.g., 'satya.prakash')
- `context_limit` (query, optional): Number of previous/next messages (1-50, default: 10)
- `search_limit` (query, optional): Maximum messages to search (1-100, default: 20)

**Example:**
```bash
curl "http://localhost:8000/slack/user/satya.prakash/messages?context_limit=10&search_limit=20"
```

### Summary Endpoint

```
GET /slack/user/{username}/messages/summary
```

Get a lightweight summary without full context.

### Health Check

```
GET /slack/health
```

Check Slack API connection status.

### Generic Search

```
GET /slack/search?query=@username&limit=20
```

Generic message search functionality.

## Response Structure

The main endpoint returns a structured response:

```json
{
  "user_id": "satya.prakash",
  "username": "satya.prakash", 
  "total_messages_found": 3,
  "messages_with_context": [
    {
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
  ],
  "search_parameters": {
    "context_limit": 10,
    "search_limit": 20,
    "search_query": "@satya.prakash"
  },
  "timestamp": "2025-01-10T10:30:00Z"
}
```

## Setup

### 1. Environment Variables

Create a `.env` file with your Slack OAuth token:

```bash
SLACK_OAUTH_TOKEN=xoxp-your-slack-token-here
```

### 2. Required Slack Scopes

Your Slack app needs these OAuth scopes:
- `search:read` - For searching messages
- `channels:history` - For reading channel message history
- `groups:history` - For reading private channel history
- `im:history` - For reading direct message history
- `mpim:history` - For reading group direct message history

### 3. Install Dependencies

```bash
pip install fastapi uvicorn requests python-dotenv pydantic
```

### 4. Run the Server

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Implementation Details

### Workflow Implementation

The API follows the exact workflow from your curl commands:

1. **Step 1**: Search messages using `search.messages` API
   ```python
   # Equivalent to:
   # curl "https://slack.com/api/search.messages?query=@satya.prakash&sort=timestamp"
   ```

2. **Step 2**: For each found message, fetch context:
   ```python
   # Previous messages (equivalent to):
   # curl "https://slack.com/api/conversations.history?channel=D09E7BBKUE9&latest=1757486516.496349&limit=10&inclusive=true"
   
   # Next messages (equivalent to):
   # curl "https://slack.com/api/conversations.history?channel=D09E7BBKUE9&oldest=1757486516.496349&limit=10&inclusive=true"
   ```

3. **Step 3**: Get replies to each message:
   ```python
   # Equivalent to:
   # curl "https://slack.com/api/conversations.replies?channel=D09E7BBKUE9&ts=1757486516.496349"
   ```

### Error Handling

The API includes comprehensive error handling:

- **Authentication Errors**: Invalid or expired tokens
- **Rate Limiting**: Automatic detection and appropriate HTTP status codes
- **Network Errors**: Connection timeouts and failures
- **Permission Errors**: Insufficient scopes or channel access
- **Data Parsing Errors**: Invalid response formats

### Logging

Detailed logging is provided for:
- API initialization and token validation
- Message search operations
- Context fetching for each message
- Reply retrieval
- Error conditions and debugging information

## Testing

Test the API with the provided sample data:

```bash
# Health check
curl "http://localhost:8000/slack/health"

# Get messages for a user
curl "http://localhost:8000/slack/user/satya.prakash/messages"

# Get summary only
curl "http://localhost:8000/slack/user/satya.prakash/messages/summary"
```

## Architecture

- **SlackAPI Class**: Core functionality for Slack Web API interaction
- **Pydantic Models**: Data validation and serialization
- **FastAPI Endpoints**: RESTful API with automatic documentation
- **Custom Exceptions**: Specific error types for better error handling
- **Modular Design**: Separate modules for different concerns

The implementation is production-ready with proper error handling, logging, and documentation.
