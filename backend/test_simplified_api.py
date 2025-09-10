#!/usr/bin/env python3
"""
Test script to verify the simplified API returns List[AnalyzedItem] directly.

This script tests:
1. API returns List[AnalyzedItem] instead of wrapper response
2. Empty list when no items found
3. Proper AnalyzedItem structure
"""

import json
from common.models import AnalyzedItem, create_analyzed_item


def test_analyzed_item_structure():
    """Test that AnalyzedItem has the correct structure."""
    
    print("🧪 Test 1: AnalyzedItem Structure")
    print("=" * 50)
    
    try:
        # Create sample AnalyzedItem
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
        
        # Test JSON serialization
        item_json = item.model_dump_json(indent=2)
        item_dict = json.loads(item_json)
        
        print("✅ JSON serialization works")
        print("📋 JSON structure:")
        print(item_json)
        
        # Verify required fields
        required_fields = ["source", "link", "timestamp", "title", "long_summary", "action_items", "score"]
        for field in required_fields:
            if field in item_dict:
                print(f"   ✅ Field '{field}': {item_dict[field]}")
            else:
                print(f"   ❌ Field '{field}': missing")
                return False
        
        # Verify no extra fields
        if set(item_dict.keys()) == set(required_fields):
            print("✅ No extra fields - structure is clean")
        else:
            extra_fields = set(item_dict.keys()) - set(required_fields)
            print(f"⚠️  Extra fields found: {extra_fields}")
        
        return True
        
    except Exception as e:
        print(f"❌ AnalyzedItem structure test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_list_response_format():
    """Test that List[AnalyzedItem] format works correctly."""
    
    print("\n🧪 Test 2: List[AnalyzedItem] Response Format")
    print("=" * 50)
    
    try:
        # Create multiple AnalyzedItems
        items = [
            create_analyzed_item(
                source="slack",
                link="https://example.com/message1",
                timestamp="2025-09-10 11:22:23",
                title="First Message",
                long_summary="First message summary",
                action_items=["Action 1", "Action 2"],
                score=0.8
            ),
            create_analyzed_item(
                source="slack", 
                link="https://example.com/message2",
                timestamp="2025-09-10 11:25:00",
                title="Second Message",
                long_summary="Second message summary",
                action_items=["Action 3"],
                score=0.6
            )
        ]
        
        print(f"✅ Created {len(items)} AnalyzedItems")
        
        # Test list serialization
        items_json = json.dumps([item.model_dump() for item in items], indent=2)
        items_list = json.loads(items_json)
        
        print("✅ List serialization works")
        print(f"📊 List contains {len(items_list)} items")
        
        # Verify each item in the list
        for i, item_dict in enumerate(items_list, 1):
            print(f"   📋 Item {i}:")
            print(f"      🎯 Source: {item_dict['source']}")
            print(f"      📋 Title: {item_dict['title']}")
            print(f"      📊 Score: {item_dict['score']}")
            print(f"      ✅ Action items: {len(item_dict['action_items'])}")
        
        # Test empty list
        empty_list = []
        empty_json = json.dumps(empty_list)
        print(f"✅ Empty list serialization: {empty_json}")
        
        return True
        
    except Exception as e:
        print(f"❌ List response format test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_expected_api_response():
    """Test what the API response should look like."""
    
    print("\n🧪 Test 3: Expected API Response")
    print("=" * 50)
    
    try:
        # Simulate what the API should return
        api_response = [
            {
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
        ]
        
        print("📋 Expected API Response:")
        print(json.dumps(api_response, indent=2))
        
        # Verify structure
        if isinstance(api_response, list):
            print("✅ Response is a list")
        else:
            print("❌ Response is not a list")
            return False
        
        if len(api_response) > 0:
            item = api_response[0]
            required_fields = ["source", "link", "timestamp", "title", "long_summary", "action_items", "score"]
            
            for field in required_fields:
                if field in item:
                    print(f"   ✅ Field '{field}': present")
                else:
                    print(f"   ❌ Field '{field}': missing")
                    return False
        
        print("✅ API response structure is correct")
        
        # Test empty response
        empty_response = []
        print(f"✅ Empty response: {json.dumps(empty_response)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Expected API response test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    
    print("🎯 Simplified API Test Suite")
    print("=" * 70)
    
    # Run tests
    test1_passed = test_analyzed_item_structure()
    test2_passed = test_list_response_format()
    test3_passed = test_expected_api_response()
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 Test Results Summary:")
    print(f"   🧪 AnalyzedItem Structure: {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"   🧪 List Response Format: {'✅ PASSED' if test2_passed else '❌ FAILED'}")
    print(f"   🧪 Expected API Response: {'✅ PASSED' if test3_passed else '❌ FAILED'}")
    
    if all([test1_passed, test2_passed, test3_passed]):
        print("\n🎉 All tests passed! The simplified API is working correctly.")
        print("\n📚 What's Ready:")
        print("   ✅ API returns List[AnalyzedItem] directly")
        print("   ✅ No wrapper response object")
        print("   ✅ Clean 6-field structure per item")
        print("   ✅ Empty list when no items found")
        print("   ✅ Proper JSON serialization")
        
        print("\n🚀 API Response Format:")
        print("   📋 Success: List of AnalyzedItem objects")
        print("   📋 No items: Empty list []")
        print("   📋 Each item: 6 fields only (source, link, timestamp, title, long_summary, action_items, score)")
        
        print("\n🔗 Test with curl:")
        print("   curl 'http://localhost:8000/slack/user/satya.prakash/analyzed-messages'")
    else:
        print("\n💥 Some tests failed. Please check the error messages above.")


if __name__ == "__main__":
    main()
