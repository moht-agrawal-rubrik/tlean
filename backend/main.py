from fastapi import FastAPI, HTTPException
from slack.endpoints import router as slack_router
from dotenv import load_dotenv
import logging
import httpx
import asyncio
from typing import List
from common.models import AnalyzedItem

load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

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
            "combined_direct": "/combined/analyzed-items (Direct function calls)",
            "combined_http": "/combined/analyzed-items-http (🔥 RECOMMENDED: HTTP calls to endpoints)",
            "github": "/github/prs" if GITHUB_ROUTER_AVAILABLE else "Not available",
            "jira": "/jira/issues" if JIRA_ROUTER_AVAILABLE else "Not available",
            "slack": "/slack/analyzed-messages",
            "slack_detailed": {
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


# Combined endpoint that aggregates all integrations
@app.get("/combined/analyzed-items", response_model=List[AnalyzedItem])
async def get_combined_analyzed_items():
    """
    Get analyzed items from all available integrations (GitHub, JIRA, Slack)
    and return them ranked by score in descending order.

    This endpoint:
    1. Calls /github/prs (if available)
    2. Calls /jira/issues (if available)
    3. Calls /slack/analyzed-messages (always available)
    4. Combines all results
    5. Sorts by score (highest first)
    6. Returns unified List[AnalyzedItem]

    Uses default usernames/profiles for testing purposes.

    Returns:
        List[AnalyzedItem]: Combined and ranked results from all integrations
    """

    logger.info("🔄 Starting combined analysis from all integrations")

    all_items = []

    # Import and call functions directly (much more efficient than HTTP calls)

    # 1. Fetch GitHub PRs (if available)
    if GITHUB_ROUTER_AVAILABLE:
        try:
            logger.info("📊 Checking GitHub integration...")

            # Check if the module and function exist
            try:
                from github.github_router import get_user_prs
                if not callable(get_user_prs):
                    raise AttributeError("get_user_prs is not callable")
                logger.info("✅ GitHub function found and callable")
            except ImportError as e:
                logger.error(f"❌ GitHub: Import error - {e}")
                raise
            except AttributeError as e:
                logger.error(f"❌ GitHub: Function not found or not callable - {e}")
                raise

            # Try to call the function
            logger.info("📊 Fetching GitHub PRs...")
            github_items = await get_user_prs()

            if isinstance(github_items, list):
                logger.info(f"✅ GitHub: Retrieved {len(github_items)} items")
                all_items.extend(github_items)
            else:
                logger.warning(f"⚠️  GitHub: Response is not a list (got {type(github_items)}), skipping")

        except Exception as e:
            logger.error(f"❌ GitHub: Failed to fetch PRs - {e}")
            logger.debug(f"   GitHub error details: {type(e).__name__}: {str(e)}")
    else:
        logger.info("⚠️  GitHub integration not available")

    # 2. Fetch JIRA issues (if available)
    if JIRA_ROUTER_AVAILABLE:
        try:
            logger.info("📊 Checking JIRA integration...")

            # Check if the module and function exist
            try:
                from jira_integration.jira_router import get_user_issues
                if not callable(get_user_issues):
                    raise AttributeError("get_user_issues is not callable")
                logger.info("✅ JIRA function found and callable")
            except ImportError as e:
                logger.error(f"❌ JIRA: Import error - {e}")
                raise
            except AttributeError as e:
                logger.error(f"❌ JIRA: Function not found or not callable - {e}")
                raise

            # Try to call the function
            logger.info("📊 Fetching JIRA issues...")
            jira_items = await get_user_issues()

            if isinstance(jira_items, list):
                logger.info(f"✅ JIRA: Retrieved {len(jira_items)} items")
                all_items.extend(jira_items)
            else:
                logger.warning(f"⚠️  JIRA: Response is not a list (got {type(jira_items)}), skipping")

        except Exception as e:
            logger.error(f"❌ JIRA: Failed to fetch issues - {e}")
            logger.debug(f"   JIRA error details: {type(e).__name__}: {str(e)}")
    else:
        logger.info("⚠️  JIRA integration not available")

    # 3. Fetch Slack analyzed messages (always available)
    try:
        logger.info("📊 Fetching Slack analyzed messages...")
        from slack.endpoints import get_analyzed_user_messages, get_slack_api

        # Get SlackAPI instance using dependency
        slack_api = get_slack_api()
        slack_items = await get_analyzed_user_messages(
            username=None,  # Uses default username
            context_limit=10,
            search_limit=20,
            slack_api=slack_api
        )

        if isinstance(slack_items, list):
            logger.info(f"✅ Slack: Retrieved {len(slack_items)} items")
            all_items.extend(slack_items)
        else:
            logger.warning("⚠️  Slack: Response is not a list, skipping")

    except Exception as e:
        logger.error(f"❌ Slack: Failed to fetch analyzed messages - {e}")

    logger.info(f"📊 Total items collected: {len(all_items)}")

    # Convert dictionaries to AnalyzedItem objects if needed
    analyzed_items = []
    for item in all_items:
        try:
            if isinstance(item, dict):
                # Create AnalyzedItem from dictionary
                analyzed_item = AnalyzedItem(**item)
                analyzed_items.append(analyzed_item)
            elif isinstance(item, AnalyzedItem):
                analyzed_items.append(item)
            else:
                logger.warning(f"⚠️  Skipping unknown item type: {type(item)}")
        except Exception as e:
            logger.error(f"❌ Failed to convert item to AnalyzedItem: {e}")
            logger.debug(f"   Item data: {item}")
            continue

    # Sort by score in descending order (highest score first)
    analyzed_items.sort(key=lambda x: x.score, reverse=True)

    logger.info(f"✅ Combined analysis complete: {len(analyzed_items)} items ranked by score")

    # Log score distribution
    if analyzed_items:
        highest_score = analyzed_items[0].score
        lowest_score = analyzed_items[-1].score
        logger.info(f"📊 Score range: {highest_score:.3f} (highest) to {lowest_score:.3f} (lowest)")

        # Log top 3 items
        for i, item in enumerate(analyzed_items[:3], 1):
            logger.info(f"   🏆 #{i}: {item.source} - {item.title[:50]}... (score: {item.score:.3f})")

    return analyzed_items


# HTTP-based combined endpoint (more reliable)
@app.get("/combined/analyzed-items-http", response_model=List[AnalyzedItem])
async def get_combined_analyzed_items_http():
    """
    Get analyzed items from all available integrations using HTTP calls.

    This endpoint:
    1. Makes HTTP calls to /github/prs (if available)
    2. Makes HTTP calls to /jira/issues (if available)
    3. Makes HTTP calls to /slack/analyzed-messages (always available)
    4. Combines all results
    5. Sorts by score (highest first)
    6. Returns unified List[AnalyzedItem]

    Uses HTTP client calls to actual API endpoints for maximum reliability.

    Returns:
        List[AnalyzedItem]: Combined and ranked results from all integrations
    """

    logger.info("🌐 Starting HTTP-based combined analysis from all integrations")

    all_items = []
    base_url = "http://localhost:8000"

    # Use httpx client for HTTP calls with 10 minute timeout
    async with httpx.AsyncClient(base_url=base_url, timeout=600.0) as client:

        # Define endpoints to call
        endpoints = []

        # 1. GitHub PRs (if available)
        if GITHUB_ROUTER_AVAILABLE:
            endpoints.append(("github", "/github/prs"))
            logger.info("📊 Will call GitHub endpoint: /github/prs")
        else:
            logger.info("⚠️  GitHub integration not available")

        # 2. JIRA issues (if available)
        if JIRA_ROUTER_AVAILABLE:
            endpoints.append(("jira", "/jira/issues"))
            logger.info("📊 Will call JIRA endpoint: /jira/issues")
        else:
            logger.info("⚠️  JIRA integration not available")

        # 3. Slack analyzed messages (always available)
        endpoints.append(("slack", "/slack/analyzed-messages"))
        logger.info("📊 Will call Slack endpoint: /slack/analyzed-messages")

        logger.info(f"🚀 Making {len(endpoints)} HTTP requests in parallel")

        # Create tasks for parallel execution
        tasks = []
        for source, endpoint in endpoints:
            task = asyncio.create_task(
                make_http_request(client, source, endpoint),
                name=f"{source}_request"
            )
            tasks.append(task)

        # Execute all requests in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        for i, result in enumerate(results):
            source = endpoints[i][0]

            if isinstance(result, Exception):
                logger.error(f"❌ {source}: Request failed with exception - {result}")
                continue

            if result is None:
                logger.warning(f"⚠️  {source}: No data returned")
                continue

            if isinstance(result, list):
                logger.info(f"✅ {source}: Retrieved {len(result)} items")
                all_items.extend(result)
            else:
                logger.warning(f"⚠️  {source}: Response is not a list (got {type(result)}), skipping")

    logger.info(f"📊 Total items collected via HTTP: {len(all_items)}")

    # Convert dictionaries to AnalyzedItem objects if needed
    analyzed_items = []
    for item in all_items:
        try:
            if isinstance(item, dict):
                # Create AnalyzedItem from dictionary
                analyzed_item = AnalyzedItem(**item)
                analyzed_items.append(analyzed_item)
            elif isinstance(item, AnalyzedItem):
                analyzed_items.append(item)
            else:
                logger.warning(f"⚠️  Skipping unknown item type: {type(item)}")
        except Exception as e:
            logger.error(f"❌ Failed to convert item to AnalyzedItem: {e}")
            logger.debug(f"   Item data: {item}")
            continue

    # Sort by score in descending order (highest score first)
    analyzed_items.sort(key=lambda x: x.score, reverse=True)

    logger.info(f"✅ HTTP-based combined analysis complete: {len(analyzed_items)} items ranked by score")

    # Log score distribution
    if analyzed_items:
        highest_score = analyzed_items[0].score
        lowest_score = analyzed_items[-1].score
        logger.info(f"📊 Score range: {highest_score:.3f} (highest) to {lowest_score:.3f} (lowest)")

        # Log top 3 items
        for i, item in enumerate(analyzed_items[:3], 1):
            logger.info(f"   🏆 #{i}: {item.source} - {item.title[:50]}... (score: {item.score:.3f})")

    return analyzed_items


async def make_http_request(client: httpx.AsyncClient, source: str, endpoint: str) -> List[dict]:
    """
    Make HTTP request to a specific endpoint.

    Args:
        client: httpx AsyncClient instance
        source: Source name for logging (github, jira, slack)
        endpoint: API endpoint to call

    Returns:
        List of items from the endpoint, or empty list if failed
    """
    try:
        logger.info(f"📤 Making HTTP request to {source}: {endpoint}")

        response = await client.get(endpoint)

        if response.status_code == 200:
            data = response.json()

            if isinstance(data, list):
                logger.info(f"✅ {source}: HTTP 200, {len(data)} items")
                return data
            else:
                logger.warning(f"⚠️  {source}: HTTP 200 but response is not a list")
                return []
        else:
            logger.error(f"❌ {source}: HTTP {response.status_code}")
            logger.debug(f"   Response: {response.text[:200]}...")
            return []

    except httpx.TimeoutException:
        logger.error(f"❌ {source}: Request timeout")
        return []
    except httpx.ConnectError:
        logger.error(f"❌ {source}: Connection error")
        return []
    except Exception as e:
        logger.error(f"❌ {source}: Unexpected error - {e}")
        return []
