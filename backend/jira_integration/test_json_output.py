#!/usr/bin/env python3
"""
Test script for JIRA JSON output functionality.
This script demonstrates how to use the new JSON output function.
"""

import json
import sys
import os
import importlib.util

# Add the parent directory to the path so we can import jira-main
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import from jira-main.py using importlib
spec = importlib.util.spec_from_file_location("jira_main", "jira-main.py")
jira_main = importlib.util.module_from_spec(spec)
spec.loader.exec_module(jira_main)

generate_jira_json_output = jira_main.generate_jira_json_output
JiraJSONProcessor = jira_main.JiraJSONProcessor


def test_json_output():
    """Test the JSON output functionality."""
    print("🔍 Testing JIRA JSON Output Generation")
    print("=" * 50)
    
    try:
        # Generate JSON output
        print("📋 Fetching JIRA issues and generating JSON output...")
        json_results = generate_jira_json_output()
        
        if not json_results:
            print("❌ No JIRA issues found or processed.")
            return
        
        print(f"✅ Successfully processed {len(json_results)} JIRA issues")
        print("\n📄 JSON Output:")
        print("=" * 50)
        
        # Pretty print the JSON
        print(json.dumps(json_results, indent=2))
        
        # Save to file for inspection
        output_file = "jira_output.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(json_results, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Output saved to: {output_file}")
        
        # Show summary statistics
        print(f"\n📊 Summary Statistics:")
        print(f"- Total issues: {len(json_results)}")
        
        if json_results:
            scores = [item['score'] for item in json_results]
            avg_score = sum(scores) / len(scores)
            max_score = max(scores)
            min_score = min(scores)
            
            print(f"- Average urgency score: {avg_score:.2f}")
            print(f"- Highest urgency score: {max_score:.2f}")
            print(f"- Lowest urgency score: {min_score:.2f}")
            
            total_action_items = sum(len(item['action_items']) for item in json_results)
            print(f"- Total action items: {total_action_items}")
            
            # Show sample entry
            print(f"\n📋 Sample Entry:")
            print("-" * 30)
            sample = json_results[0]
            print(f"Title: {sample['title']}")
            print(f"Score: {sample['score']}")
            print(f"Action Items: {len(sample['action_items'])}")
            print(f"Timestamp: {sample['timestamp']}")
            print(f"Link: {sample['link']}")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()


def test_single_issue():
    """Test processing a single JIRA issue."""
    print("\n🔍 Testing Single Issue Processing")
    print("=" * 50)
    
    # You can modify this to test with a specific JIRA key
    test_key = "CDM-474480"  # Replace with an actual JIRA key from your system
    
    try:
        processor = JiraJSONProcessor()
        json_results = processor.convert_jira_to_json([test_key])
        
        if json_results:
            print(f"✅ Successfully processed issue: {test_key}")
            print(json.dumps(json_results[0], indent=2))
        else:
            print(f"❌ Failed to process issue: {test_key}")
            
    except Exception as e:
        print(f"❌ Error processing single issue: {e}")


if __name__ == "__main__":
    print("🧪 JIRA JSON Output Test Suite")
    print("=" * 50)
    
    # Test the full JSON output
    test_json_output()
    
    # Uncomment to test single issue processing
    # test_single_issue()
    
    print("\n✅ Testing complete!")
