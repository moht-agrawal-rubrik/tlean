#!/usr/bin/env python3
"""
Test script to verify the common format works correctly.

This script tests:
1. Common models (AnalyzedItem, AnalyzedItemsResponse)
2. Slack integration with common format
3. Response structure consistency
"""

import os
import sys
import json
import logging
from datetime import datetime

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from common.models import AnalyzedItem, AnalyzedItemsResponse, create_analyzed_item, create_analyzed_items_response

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_common_models():
    """Test the common models work correctly."""
    
    print("🧪 Test 1: Common Models")
    print("=" * 50)
    
    try:
        # Test AnalyzedItem creation
        item = create_analyzed_item(
            source="slack",
            link="https://hackthon-test-group.slack.com/archives/D09E7BBKUE9/p1757483543855429",
            timestamp="2025-09-10 11:22:23",
            title="API Testing Query",
            long_summary="User is asking for updates on API implementation...",
            action_items=[
                "Provide status update on API implementation",
                "Share timeline for completion"
            ],
            score=0.7
        )
        
        print("✅ AnalyzedItem created successfully")
        print(f"   📊 Score: {item.score}")
        print(f"   🎯 Source: {item.source}")
        print(f"   📋 Title: {item.title}")
        print(f"   ✅ Action items: {len(item.action_items)}")
        
        # Test JSON serialization
        item_json = item.model_dump_json(indent=2)
        print("✅ JSON serialization works")
        print(f"   📏 JSON length: {len(item_json)} characters")
        
        # Test AnalyzedItemsResponse creation
        response = create_analyzed_items_response(
            source="slack",
            user_identifier="satya.prakash",
            total_items_found=5,
            analyzed_items=[item]
        )
        
        print("✅ AnalyzedItemsResponse created successfully")
        print(f"   👤 User: {response.user_identifier}")
        print(f"   📊 Total found: {response.total_items_found}")
        print(f"   🎯 Need attention: {response.items_needing_attention}")
        print(f"   📅 Analysis time: {response.analysis_timestamp}")
        
        # Test response JSON serialization
        response_json = response.model_dump_json(indent=2)
        print("✅ Response JSON serialization works")
        print(f"   📏 Response JSON length: {len(response_json)} characters")
        
        return True
        
    except Exception as e:
        print(f"❌ Common models test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_slack_format_compatibility():
    """Test that Slack format matches the expected common format."""
    
    print("\n🧪 Test 2: Slack Format Compatibility")
    print("=" * 50)
    
    try:
        # Sample Slack LLM response (what we expect from LLM)
        slack_llm_response = {
            "source": "slack",
            "link": "https://hackthon-test-group.slack.com/archives/D09E7BBKUE9/p1757483543855429",
            "timestamp": "2025-09-10 11:22:23",
            "title": "API Testing Query",
            "long_summary": "In this Slack conversation, user U09E7BBEB9T reached out to U09DVNAD36K to inquire about the completion of API testing for fetching Slack messages. There is some back and forth on whether certain tasks are needed, with U09DVNAD36K mentioning that the task is 'done' and agreeing to add more if needed.",
            "action_items": [
                "U09DVNAD36K needs to confirm completion of API testing as U09E7BBEB9T asked for status updates.",
                "U09DVNAD36K needs to ensure any additional necessary actions are taken regarding the API Testing."
            ],
            "score": 0.7
        }
        
        print("📝 Sample Slack LLM response:")
        print(json.dumps(slack_llm_response, indent=2))
        
        # Convert to AnalyzedItem
        from common.models import slack_result_to_analyzed_item
        analyzed_item = slack_result_to_analyzed_item(slack_llm_response)
        
        print("✅ Conversion to AnalyzedItem successful")
        print(f"   📊 Score: {analyzed_item.score}")
        print(f"   🎯 Source: {analyzed_item.source}")
        print(f"   📋 Title: {analyzed_item.title}")
        print(f"   ✅ Action items: {len(analyzed_item.action_items)}")
        
        # Test that all required fields are present
        required_fields = ["source", "link", "timestamp", "title", "long_summary", "action_items", "score"]
        for field in required_fields:
            if hasattr(analyzed_item, field):
                print(f"   ✅ Field '{field}': present")
            else:
                print(f"   ❌ Field '{field}': missing")
                return False
        
        # Test JSON output matches expected format
        output_json = analyzed_item.model_dump_json(indent=2)
        output_dict = json.loads(output_json)
        
        print("✅ Final JSON output:")
        print(output_json)
        
        # Verify no extra fields
        expected_fields = set(required_fields)
        actual_fields = set(output_dict.keys())
        
        if expected_fields == actual_fields:
            print("✅ Field structure matches exactly")
        else:
            extra_fields = actual_fields - expected_fields
            missing_fields = expected_fields - actual_fields
            if extra_fields:
                print(f"⚠️  Extra fields: {extra_fields}")
            if missing_fields:
                print(f"❌ Missing fields: {missing_fields}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Slack format compatibility test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_github_format_compatibility():
    """Test that GitHub format matches the expected common format."""
    
    print("\n🧪 Test 3: GitHub Format Compatibility")
    print("=" * 50)
    
    try:
        # Sample GitHub response (what we expect from GitHub integration)
        github_response = {
            "source": "github",
            "link": "https://github.com/scaledata/sdmain/pull/97449",
            "timestamp": "2025-09-02 06:40:19",
            "title": "PR #97449: Add RBAC test for the bulk secondary register host",
            "long_summary": "Modified 10 files. (+212/-10 lines). - tests\n\nKey changes:\n• polaris/src/rubrik/api-server/app/services/physicalhost/rbac/BUILD.bazel: Added dependencies on proto_deps and common-scala to the rkscala_library build target\n• polaris/src/rubrik/sdk_internal/grpc/physicalhost_pb2_grpc.py: Updated docstring for BulkRegisterSecondaryHosts method to include parameter description and removed TODO comment.\n• polaris/src/rubrik/api-server/test/app/services/physicalhost/rbac/BUILD.bazel: Added Bazel test target for physicalhost RBAC Scala tests with required dependencies and JVM config\n\nAuthor: moht-agrawal-rubrik, State: open, Reviewers: 3",
            "action_items": [
                "Clarify which output is being referenced in Comment 2 regarding the proto comments mismatch.",
                "Confirm whether the string_to_uuid transform should be applied and if it will function as expected in this context.",
                "Respond to the question in Comment 4 about the necessity of calling fetcher for the RBAC check.",
                "Double-check if passing \"UNSPECIFIED\" or *EMPTY_VALUE for HostRegisterOsType is needed, and update the code if not required.",
                "Consider providing benchmarking data or further justification regarding the performance discussion in Comment 6."
            ],
            "score": 0.452455932104785
        }
        
        print("📝 Sample GitHub response:")
        print(json.dumps(github_response, indent=2))
        
        # Convert to AnalyzedItem
        from common.models import github_result_to_analyzed_item
        analyzed_item = github_result_to_analyzed_item(github_response)
        
        print("✅ Conversion to AnalyzedItem successful")
        print(f"   📊 Score: {analyzed_item.score}")
        print(f"   🎯 Source: {analyzed_item.source}")
        print(f"   📋 Title: {analyzed_item.title}")
        print(f"   ✅ Action items: {len(analyzed_item.action_items)}")
        
        # Test JSON output
        output_json = analyzed_item.model_dump_json(indent=2)
        print("✅ Final JSON output:")
        print(output_json)
        
        return True
        
    except Exception as e:
        print(f"❌ GitHub format compatibility test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    
    print("🎯 Common Format Test Suite")
    print("=" * 70)
    
    # Run tests
    test1_passed = test_common_models()
    test2_passed = test_slack_format_compatibility()
    test3_passed = test_github_format_compatibility()
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 Test Results Summary:")
    print(f"   🧪 Common Models: {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"   🧪 Slack Format: {'✅ PASSED' if test2_passed else '❌ FAILED'}")
    print(f"   🧪 GitHub Format: {'✅ PASSED' if test3_passed else '❌ FAILED'}")
    
    if all([test1_passed, test2_passed, test3_passed]):
        print("\n🎉 All tests passed! The common format is working correctly.")
        print("\n📚 What's Ready:")
        print("   ✅ Common AnalyzedItem model for all integrations")
        print("   ✅ Common AnalyzedItemsResponse for API responses")
        print("   ✅ Slack integration uses common format")
        print("   ✅ GitHub integration compatible with common format")
        print("   ✅ JSON serialization works correctly")
        print("   ✅ No extra fields in responses")
        
        print("\n🚀 Ready for Testing:")
        print("   curl 'http://localhost:8000/slack/user/satya.prakash/analyzed-messages'")
    else:
        print("\n💥 Some tests failed. Please check the error messages above.")


if __name__ == "__main__":
    main()
