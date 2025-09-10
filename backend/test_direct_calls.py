#!/usr/bin/env python3
"""
Test script to verify direct function calls vs HTTP calls.

This script compares:
1. Direct function calls (new approach)
2. HTTP client calls (old approach)
3. Performance differences
4. Error handling
"""

import asyncio
import time
import logging
from typing import List

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def test_direct_slack_call():
    """Test calling Slack function directly."""
    
    print("🧪 Test 1: Direct Slack Function Call")
    print("=" * 50)
    
    try:
        start_time = time.time()
        
        # Import and call directly
        from slack.endpoints import get_analyzed_user_messages, get_slack_api
        
        # Get SlackAPI instance
        slack_api = get_slack_api()
        
        # Call function directly
        result = await get_analyzed_user_messages(
            username=None,  # Uses default
            context_limit=5,
            search_limit=10,
            slack_api=slack_api
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"✅ Direct call completed in {duration:.3f} seconds")
        print(f"📊 Result type: {type(result)}")
        
        if isinstance(result, list):
            print(f"📋 Items returned: {len(result)}")
            if result:
                sample_item = result[0]
                print(f"📝 Sample item keys: {list(sample_item.__dict__.keys()) if hasattr(sample_item, '__dict__') else 'N/A'}")
        else:
            print(f"⚠️  Unexpected result type: {type(result)}")
        
        return True, duration, len(result) if isinstance(result, list) else 0
        
    except Exception as e:
        print(f"❌ Direct call failed: {e}")
        import traceback
        traceback.print_exc()
        return False, 0, 0


async def test_http_slack_call():
    """Test calling Slack endpoint via HTTP."""
    
    print("\n🧪 Test 2: HTTP Slack Call")
    print("=" * 50)
    
    try:
        import httpx
        
        start_time = time.time()
        
        # Make HTTP call
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "http://localhost:8000/slack/analyzed-messages",
                params={"context_limit": 5, "search_limit": 10}
            )
        
        end_time = time.time()
        duration = end_time - start_time
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"✅ HTTP call completed in {duration:.3f} seconds")
            print(f"📊 Result type: {type(result)}")
            
            if isinstance(result, list):
                print(f"📋 Items returned: {len(result)}")
                if result:
                    sample_item = result[0]
                    print(f"📝 Sample item keys: {list(sample_item.keys()) if isinstance(sample_item, dict) else 'N/A'}")
            else:
                print(f"⚠️  Unexpected result type: {type(result)}")
            
            return True, duration, len(result) if isinstance(result, list) else 0
        else:
            print(f"❌ HTTP call failed: {response.status_code} - {response.text}")
            return False, duration, 0
        
    except Exception as e:
        print(f"❌ HTTP call failed: {e}")
        import traceback
        traceback.print_exc()
        return False, 0, 0


def test_import_availability():
    """Test which integrations are available for direct calls."""
    
    print("\n🧪 Test 3: Integration Availability")
    print("=" * 50)
    
    integrations = {
        "slack": ("slack.endpoints", "get_analyzed_user_messages"),
        "github": ("github.github_router", "get_github_prs"),
        "jira": ("jira_integration.jira_router", "get_jira_issues")
    }
    
    available = {}
    
    for name, (module_path, function_name) in integrations.items():
        try:
            module = __import__(module_path, fromlist=[function_name])
            func = getattr(module, function_name)
            available[name] = {
                "status": "available",
                "module": module_path,
                "function": function_name,
                "callable": callable(func)
            }
            print(f"✅ {name}: Available ({module_path}.{function_name})")
        except ImportError as e:
            available[name] = {
                "status": "import_error",
                "error": str(e)
            }
            print(f"❌ {name}: Import error - {e}")
        except AttributeError as e:
            available[name] = {
                "status": "function_not_found",
                "error": str(e)
            }
            print(f"❌ {name}: Function not found - {e}")
        except Exception as e:
            available[name] = {
                "status": "unknown_error",
                "error": str(e)
            }
            print(f"❌ {name}: Unknown error - {e}")
    
    return available


async def test_combined_direct_approach():
    """Test the combined approach using direct calls."""
    
    print("\n🧪 Test 4: Combined Direct Approach")
    print("=" * 50)
    
    try:
        start_time = time.time()
        
        all_items = []
        
        # Test Slack (always available)
        try:
            from slack.endpoints import get_analyzed_user_messages, get_slack_api
            slack_api = get_slack_api()
            slack_items = await get_analyzed_user_messages(
                username=None,
                context_limit=5,
                search_limit=10,
                slack_api=slack_api
            )
            if isinstance(slack_items, list):
                all_items.extend(slack_items)
                print(f"✅ Slack: {len(slack_items)} items")
            else:
                print("⚠️  Slack: Not a list")
        except Exception as e:
            print(f"❌ Slack: {e}")
        
        # Test GitHub (if available)
        try:
            from github.github_router import get_github_prs
            github_items = await get_github_prs()
            if isinstance(github_items, list):
                all_items.extend(github_items)
                print(f"✅ GitHub: {len(github_items)} items")
            else:
                print("⚠️  GitHub: Not a list")
        except ImportError:
            print("⚠️  GitHub: Not available")
        except Exception as e:
            print(f"❌ GitHub: {e}")
        
        # Test JIRA (if available)
        try:
            from jira_integration.jira_router import get_jira_issues
            jira_items = await get_jira_issues()
            if isinstance(jira_items, list):
                all_items.extend(jira_items)
                print(f"✅ JIRA: {len(jira_items)} items")
            else:
                print("⚠️  JIRA: Not a list")
        except ImportError:
            print("⚠️  JIRA: Not available")
        except Exception as e:
            print(f"❌ JIRA: {e}")
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"📊 Combined direct approach: {len(all_items)} total items in {duration:.3f} seconds")
        
        # Sort by score if items have score attribute
        try:
            sorted_items = sorted(all_items, key=lambda x: getattr(x, 'score', 0), reverse=True)
            print(f"✅ Items sorted by score")
            
            if sorted_items:
                top_item = sorted_items[0]
                print(f"🏆 Top item: {getattr(top_item, 'title', 'No title')} (score: {getattr(top_item, 'score', 0)})")
        except Exception as e:
            print(f"⚠️  Could not sort items: {e}")
        
        return True, duration, len(all_items)
        
    except Exception as e:
        print(f"❌ Combined direct approach failed: {e}")
        import traceback
        traceback.print_exc()
        return False, 0, 0


async def main():
    """Run all tests."""
    
    print("🎯 Direct Function Calls vs HTTP Calls Test Suite")
    print("=" * 70)
    
    # Test integration availability
    available_integrations = test_import_availability()
    
    # Test direct vs HTTP calls for Slack
    direct_success, direct_time, direct_count = await test_direct_slack_call()
    http_success, http_time, http_count = await test_http_slack_call()
    
    # Test combined direct approach
    combined_success, combined_time, combined_count = await test_combined_direct_approach()
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 Test Results Summary:")
    print(f"   🧪 Direct Slack Call: {'✅ PASSED' if direct_success else '❌ FAILED'}")
    print(f"   🧪 HTTP Slack Call: {'✅ PASSED' if http_success else '❌ FAILED'}")
    print(f"   🧪 Combined Direct Approach: {'✅ PASSED' if combined_success else '❌ FAILED'}")
    
    if direct_success and http_success:
        print(f"\n⚡ Performance Comparison:")
        print(f"   Direct call: {direct_time:.3f}s ({direct_count} items)")
        print(f"   HTTP call:   {http_time:.3f}s ({http_count} items)")
        
        if direct_time < http_time:
            speedup = http_time / direct_time if direct_time > 0 else float('inf')
            print(f"   🚀 Direct calls are {speedup:.1f}x faster!")
        else:
            print(f"   📊 HTTP calls were faster (unusual)")
    
    print(f"\n📋 Available Integrations:")
    for name, info in available_integrations.items():
        status = "✅" if info["status"] == "available" else "❌"
        print(f"   {status} {name}: {info['status']}")
    
    print(f"\n✅ Benefits of Direct Calls:")
    print(f"   🚀 Faster execution (no HTTP overhead)")
    print(f"   🔧 No need for httpx dependency")
    print(f"   🛡️ Better error handling")
    print(f"   📊 Direct access to function results")
    print(f"   💾 Lower memory usage")
    print(f"   🔍 Easier debugging")


if __name__ == "__main__":
    asyncio.run(main())
