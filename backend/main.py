from fastapi import FastAPI
from slack.endpoints import router as slack_router
from dotenv import load_dotenv
load_dotenv()

# Import routers
try:
    from github.github_router import router as github_router
    GITHUB_ROUTER_AVAILABLE = True
except ImportError as e:
    print(f"Warning: GitHub router not available: {e}")
    GITHUB_ROUTER_AVAILABLE = False

try:
    from jira_integration.jira_router import router as jira_router
    JIRA_ROUTER_AVAILABLE = True
except ImportError as e:
    print(f"Warning: JIRA router not available: {e}")
    JIRA_ROUTER_AVAILABLE = False

# Create FastAPI instance
app = FastAPI(
    title="TLean Backend API",
    description="Backend API for TLean - GitHub PR processing, JIRA issue processing, and action item generation",
    version="1.0.0"
)

# Include routers
if GITHUB_ROUTER_AVAILABLE:
    app.include_router(github_router)

if JIRA_ROUTER_AVAILABLE:
    app.include_router(jira_router)

# Include Slack router
app.include_router(slack_router)

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "TLean Backend API",
        "version": "1.0.0",
        "available_endpoints": {
            "health": "/health",
            "github": "/github/prs" if GITHUB_ROUTER_AVAILABLE else "Not available",
            "jira": "/jira/issues" if JIRA_ROUTER_AVAILABLE else "Not available",
            "slack": "/slack",
            "slack": {
                "health": "/slack/health",
                "user_messages": "/slack/user/{username}/messages",
                "user_summary": "/slack/user/{username}/messages/summary",
                "analyzed_messages": "/slack/user/{username}/analyzed-messages (LLM-powered insights)",
                "search": "/slack/search"
            },
            "docs": "/docs"
        }
    }


# Hello endpoint with a path parameter
@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "github_integration": "available" if GITHUB_ROUTER_AVAILABLE else "unavailable",
        "jira_integration": "available" if JIRA_ROUTER_AVAILABLE else "unavailable"
    }
