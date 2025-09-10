# GitHub API Router

FastAPI router for processing GitHub PR data with LLM-powered action item generation.

## Setup

### 1. Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Required variables:
- `GITHUB_TOKEN`: Your GitHub personal access token
- `GITHUB_USERNAME`: GitHub username to fetch PRs for
- `GITHUB_LIMIT`: Default number of PRs to fetch (optional, default: 10)

### 2. GitHub Token Setup

1. Go to GitHub Settings → Developer settings → Personal access tokens
2. Generate a new token with these scopes:
   - `repo` (for private repositories)
   - `public_repo` (for public repositories)
   - `read:user` (for user information)

## API Endpoints

### GET /github/prs

Get processed PR data for the configured user.

**Query Parameters:**
- `state` (optional): PR state - "open", "closed", or "all" (default: "open")
- `limit` (optional): Override default limit (1-100)

**Response:** Returns only processed data (action items, summaries, scores)

```bash
curl "http://localhost:8000/github/prs?state=open&limit=5"
```

### GET /github/prs/raw

Get complete PR data (both raw GitHub data and processed data).

**Query Parameters:**
- `state` (optional): PR state - "open", "closed", or "all" (default: "open")  
- `limit` (optional): Override default limit (1-100)

**Response:** Returns full candidate data including raw GitHub API responses

```bash
curl "http://localhost:8000/github/prs/raw?state=open&limit=5"
```

### GET /github/config

Get current configuration (without sensitive data).

```bash
curl "http://localhost:8000/github/config"
```

### GET /github/health

Health check for GitHub integration.

```bash
curl "http://localhost:8000/github/health"
```

## Response Format

### Processed Data Response (`/github/prs`)

```json
{
  "success": true,
  "message": "Successfully fetched 3 PRs for user username",
  "data": [
    {
      "source": "github",
      "link": "https://github.com/owner/repo/pull/123",
      "timestamp": "2024-01-15T10:00:00Z",
      "title": "Add user authentication service",
      "long_summary": "Implements JWT-based authentication...",
      "action_items": [
        "Address memory leak concern in UserService.cleanup() method",
        "Add unit tests for the new authentication flow as requested"
      ],
      "score": 0.75
    }
  ],
  "total_count": 3
}
```

### Raw Data Response (`/github/prs/raw`)

```json
{
  "success": true,
  "message": "Successfully fetched 3 PRs for user username",
  "data": [
    {
      "source": "github",
      "candidate_id": "github_pr_123",
      "raw_data": {
        "pr_title": "Add user authentication service",
        "pr_url": "https://github.com/owner/repo/pull/123",
        "metadata": { ... },
        "comments": { ... }
      },
      "processed_data": {
        "source": "github",
        "link": "https://github.com/owner/repo/pull/123",
        "title": "Add user authentication service",
        "action_items": [...],
        "score": 0.75
      }
    }
  ],
  "total_count": 3
}
```

## Features

- **LLM-Powered Action Items**: Uses OpenAI to analyze PR comments and generate intelligent action items
- **Bot Filtering**: Automatically filters out bot comments (rubrik-alfred[bot], etc.)
- **Configurable Limits**: Set default limits via environment variables
- **Multiple PR States**: Fetch open, closed, or all PRs
- **Health Monitoring**: Built-in health checks and configuration validation
- **Error Handling**: Comprehensive error responses with details

## Running the Server

```bash
# Install dependencies
uv sync

# Start development server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Access the API documentation at: http://localhost:8000/docs
