from fastapi import FastAPI, HTTPException
from slack.endpoints import router as slack_router
from dotenv import load_dotenv
import logging
import httpx
import asyncio
import os
from typing import List, Dict, Any
from datetime import datetime
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
            "slack_summary": "/slack/send-daily-summary (🚀 NEW: Send formatted summary to Slack)",
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


@app.post("/slack/send-daily-summary")
async def send_daily_summary_to_slack(channel_id: str = "C09E27E6F8X"):
    """
    Fetch analyzed items and send each as individual Slack messages.

    This endpoint:
    1. Fetches analyzed items from /combined/analyzed-items-http
    2. Sends each item as a separate formatted Slack message
    3. Returns success/failure status with details

    Args:
        channel_id: Slack channel ID to send the messages to

    Returns:
        Dict with status and details of all messages sent
    """

    logger.info(f"📤 Starting individual message send to Slack channel: {channel_id}")

    try:
        # 1. Fetch analyzed items from combined endpoint
        logger.info("📊 Fetching analyzed items from combined endpoint...")

        async with httpx.AsyncClient(timeout=600.0) as client:
            response = await client.get("http://localhost:8000/combined/analyzed-items-http")

            if response.status_code != 200:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to fetch analyzed items: HTTP {response.status_code}"
                )

            analyzed_items = response.json()
            logger.info(f"✅ Retrieved {len(analyzed_items)} analyzed items")

        if not analyzed_items:
            logger.info("ℹ️  No analyzed items to send")
            return {
                "status": "success",
                "message": "No items to send",
                "items_count": 0,
                "messages_sent": 0,
                "channel_id": channel_id
            }

        # 2. Send header message first
        logger.info("📤 Sending header message...")
        header_blocks = create_header_blocks(len(analyzed_items))
        await send_blocks_to_slack(channel_id, header_blocks)

        # 3. Send each item as individual message with details in thread
        logger.info(f"📤 Sending {len(analyzed_items)} individual messages with threaded details...")
        sent_messages = []
        failed_messages = []

        for i, item in enumerate(analyzed_items, 1):
            try:
                logger.debug(f"📤 Sending message {i}/{len(analyzed_items)}")

                # Create summary blocks for main message (compact)
                summary_blocks = create_summary_blocks(item, i, len(analyzed_items))

                # Send main summary message
                main_response = await send_blocks_to_slack(channel_id, summary_blocks)
                main_ts = main_response.get("ts")

                if main_ts:
                    # Create detailed blocks for thread reply
                    detail_blocks = create_detail_blocks(item)

                    # Send detailed message as thread reply
                    await send_blocks_to_slack(channel_id, detail_blocks, thread_ts=main_ts)

                    sent_messages.append({
                        "item_index": i,
                        "title": item.get("title", "Untitled"),
                        "source": item.get("source", "unknown"),
                        "main_ts": main_ts,
                        "has_thread": True
                    })
                else:
                    logger.warning(f"⚠️  No timestamp returned for message {i}, skipping thread")
                    sent_messages.append({
                        "item_index": i,
                        "title": item.get("title", "Untitled"),
                        "source": item.get("source", "unknown"),
                        "main_ts": None,
                        "has_thread": False
                    })

                # Small delay between messages to avoid rate limits
                await asyncio.sleep(0.5)

            except Exception as e:
                logger.error(f"❌ Failed to send message {i}/{len(analyzed_items)}: {e}")
                failed_messages.append({
                    "item_index": i,
                    "title": item.get("title", "Untitled"),
                    "error": str(e)
                })

        logger.info(f"✅ Sent {len(sent_messages)}/{len(analyzed_items)} messages successfully")

        return {
            "status": "success" if not failed_messages else "partial_success",
            "message": f"Sent {len(sent_messages)}/{len(analyzed_items)} messages successfully",
            "items_count": len(analyzed_items),
            "messages_sent": len(sent_messages),
            "messages_failed": len(failed_messages),
            "channel_id": channel_id,
            "sent_messages": sent_messages,
            "failed_messages": failed_messages
        }

    except Exception as e:
        logger.error(f"❌ Failed to send messages to Slack: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to send messages: {str(e)}"
        )


def create_header_blocks(items_count: int) -> List[Dict[str, Any]]:
    """
    Create header blocks for the daily summary.

    Args:
        items_count: Number of items that will be sent

    Returns:
        List of Slack blocks for the header message
    """

    blocks = []

    # Header block
    header_text = f"Daily Activity Summary - {datetime.now().strftime('%B %d, %Y')}"

    blocks.append({
        "type": "header",
        "text": {
            "type": "plain_text",
            "text": header_text,
            "emoji": True
        }
    })

    # Context block
    context_text = f"📊 Found {items_count} items requiring attention • Sending as individual messages"

    blocks.append({
        "type": "context",
        "elements": [
            {
                "type": "mrkdwn",
                "text": context_text
            }
        ]
    })

    blocks.append({"type": "divider"})

    return blocks


def create_summary_blocks(item: Dict[str, Any], item_index: int, total_items: int) -> List[Dict[str, Any]]:
    """
    Create compact summary blocks for the main channel message.

    Args:
        item: Single analyzed item from the API
        item_index: Index of this item (1-based)
        total_items: Total number of items being sent

    Returns:
        List of Slack blocks for the summary message
    """

    blocks = []

    # Item number indicator
    blocks.append({
        "type": "context",
        "elements": [
            {
                "type": "mrkdwn",
                "text": f"📋 Item {item_index} of {total_items}"
            }
        ]
    })

    try:
        # Get source emoji
        source_emoji = get_source_emoji(item.get("source", ""))

        # Priority indicator based on score
        priority_indicator = get_priority_indicator(item.get("score", 0))

        # Main section with title and link
        title = item.get("title", "Untitled")
        link = item.get("link", "#")

        # Truncate title if too long
        if len(title) > 200:
            title = title[:197] + "..."

        title_text = f"{source_emoji} {priority_indicator} *<{link}|{title}>*"

        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": title_text
            }
        })

        # Source context
        source = item.get("source", "unknown")
        source_display = source.upper()

        blocks.append({
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"📍 Source: *{source_display}* • 💬 _Reply to this thread for details_"
                }
            ]
        })

    except Exception as e:
        logger.error(f"❌ Failed to create summary block for item {item_index}: {e}")
        # Add a simple error block
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"⚠️ Error processing item {item_index}: {str(e)[:100]}"
            }
        })

    return blocks


def create_detail_blocks(item: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Create detailed blocks for the thread reply.

    Args:
        item: Single analyzed item from the API

    Returns:
        List of Slack blocks for the detailed thread message
    """

    blocks = []

    try:
        summary = item.get("long_summary", "")
        action_items = item.get("action_items", [])

        # Summary section
        if summary:
            # Truncate if too long
            if len(summary) > 2800:
                summary = summary[:2797] + "..."

            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*📄 Summary:*\n{summary}"
                }
            })

        # Action items section
        if action_items:
            action_text = "*✅ Action Items:*\n"
            for action in action_items:
                action_line = f"• {action}\n"
                # Check if adding this action would exceed limit
                if len(action_text + action_line) > 2800:
                    action_text += "• ... (more items truncated)"
                    break
                action_text += action_line

            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": action_text.strip()
                }
            })

        # If no content, add a placeholder
        if not summary and not action_items:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "ℹ️ No additional details available for this item."
                }
            })

    except Exception as e:
        logger.error(f"❌ Failed to create detail blocks: {e}")
        # Add a simple error block
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"⚠️ Error processing details: {str(e)[:100]}"
            }
        })

    return blocks


def get_source_emoji(source: str) -> str:
    """Get emoji for different sources."""
    source_emojis = {
        "github": "🐙",
        "jira": "🎫",
        "slack": "💬"
    }
    return source_emojis.get(source.lower(), "📋")


def get_priority_indicator(score: float) -> str:
    """Get priority indicator based on score."""
    if score >= 0.8:
        return "🔴 HIGH"
    elif score >= 0.6:
        return "🟡 MEDIUM"
    elif score >= 0.4:
        return "🟢 LOW"
    else:
        return "⚪ INFO"


async def send_blocks_to_slack(channel_id: str, blocks: List[Dict[str, Any]], thread_ts: str = None) -> Dict[str, Any]:
    """
    Send blocks to Slack channel using chat.postMessage API.

    Args:
        channel_id: Slack channel ID
        blocks: List of Slack blocks to send
        thread_ts: Optional thread timestamp to reply to a thread

    Returns:
        Slack API response
    """

    # Get Slack bot token from environment
    slack_bot_token = os.getenv("SLACK_BOT_TOKEN")
    if not slack_bot_token:
        raise ValueError("SLACK_BOT_TOKEN environment variable not set")

    # Prepare the payload
    payload = {
        "channel": channel_id,
        "text": "Activity Summary" if not thread_ts else "Activity Details",  # Fallback text
        "blocks": blocks
    }

    # Add thread_ts if this is a thread reply
    if thread_ts:
        payload["thread_ts"] = thread_ts

    # Send to Slack
    headers = {
        "Authorization": f"Bearer {slack_bot_token}",
        "Content-Type": "application/json; charset=utf-8"
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            "https://slack.com/api/chat.postMessage",
            headers=headers,
            json=payload
        )

        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Slack API request failed: {response.text}"
            )

        slack_response = response.json()

        if not slack_response.get("ok"):
            error_msg = slack_response.get("error", "Unknown error")
            raise HTTPException(
                status_code=400,
                detail=f"Slack API error: {error_msg}"
            )

        return slack_response
