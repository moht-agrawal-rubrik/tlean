#!/usr/bin/env python3
"""
Example usage of the JIRA JSON output functionality.
This script shows how to use the new JSON output format.
"""

import json
import importlib.util
from typing import List, Dict, Any


def load_jira_module():
    """Load the jira-main module."""
    spec = importlib.util.spec_from_file_location("jira_main", "jira-main.py")
    jira_main = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(jira_main)
    return jira_main


def example_usage():
    """Example of how to use the JIRA JSON output functionality."""
    print("📋 JIRA JSON Output Example")
    print("=" * 40)
    
    # Load the JIRA module
    jira_main = load_jira_module()
    
    # Method 1: Use the convenience function to get all assigned issues
    print("\n🔍 Method 1: Get all assigned JIRA issues as JSON")
    print("-" * 40)
    
    try:
        json_results = jira_main.generate_jira_json_output()
        
        print(f"Found {len(json_results)} JIRA issues")
        
        # Display the results
        for item in json_results:
            print(f"\n📌 {item['title']}")
            print(f"   🔗 Link: {item['link']}")
            print(f"   ⏰ Updated: {item['timestamp']}")
            print(f"   📊 Urgency Score: {item['score']}")
            print(f"   ✅ Action Items ({len(item['action_items'])}):")
            for i, action in enumerate(item['action_items'], 1):
                print(f"      {i}. {action}")
            print(f"   📝 Summary: {item['long_summary'][:100]}...")
    
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Method 2: Process specific JIRA keys
    print("\n\n🔍 Method 2: Process specific JIRA keys")
    print("-" * 40)
    
    try:
        # Replace these with actual JIRA keys from your system
        specific_keys = ["CDM-474480"]  # Add more keys as needed
        
        processor = jira_main.JiraJSONProcessor()
        specific_results = processor.convert_jira_to_json(specific_keys)
        
        print(f"Processed {len(specific_results)} specific issues")
        
        # Save to file
        output_file = "specific_jira_issues.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(specific_results, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Results saved to: {output_file}")
        
    except Exception as e:
        print(f"❌ Error processing specific keys: {e}")


def filter_by_urgency(json_results: List[Dict[str, Any]], min_score: float = 0.7) -> List[Dict[str, Any]]:
    """
    Filter JIRA issues by urgency score.
    
    Args:
        json_results: List of JIRA issues in JSON format
        min_score: Minimum urgency score to include
        
    Returns:
        Filtered list of high-urgency issues
    """
    return [item for item in json_results if item['score'] >= min_score]


def group_by_source(json_results: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Group issues by source (useful when combining with other sources like GitHub, Slack).
    
    Args:
        json_results: List of issues in JSON format
        
    Returns:
        Dictionary grouped by source
    """
    grouped = {}
    for item in json_results:
        source = item['source']
        if source not in grouped:
            grouped[source] = []
        grouped[source].append(item)
    return grouped


def example_filtering():
    """Example of filtering and grouping the JSON results."""
    print("\n\n🔍 Example: Filtering and Grouping")
    print("=" * 40)
    
    try:
        # Load the JIRA module and get results
        jira_main = load_jira_module()
        json_results = jira_main.generate_jira_json_output()
        
        if not json_results:
            print("No JIRA issues found.")
            return
        
        # Filter high-urgency issues
        high_urgency = filter_by_urgency(json_results, min_score=0.7)
        print(f"🚨 High urgency issues (score >= 0.7): {len(high_urgency)}")
        
        for item in high_urgency:
            print(f"   • {item['title']} (Score: {item['score']})")
        
        # Group by source (will all be 'jira' in this case)
        grouped = group_by_source(json_results)
        print(f"\n📊 Issues by source:")
        for source, items in grouped.items():
            print(f"   • {source}: {len(items)} issues")
        
        # Show action items summary
        total_actions = sum(len(item['action_items']) for item in json_results)
        print(f"\n✅ Total action items across all issues: {total_actions}")
        
    except Exception as e:
        print(f"❌ Error during filtering: {e}")


if __name__ == "__main__":
    print("🧪 JIRA JSON Output Usage Examples")
    print("=" * 50)
    
    # Run the examples
    example_usage()
    example_filtering()
    
    print("\n✅ Examples complete!")
    print("\nThe JSON format includes:")
    print("- source: 'jira'")
    print("- link: Direct link to the JIRA issue")
    print("- timestamp: Last updated time in UTC")
    print("- title: Issue key and summary (max 200 chars)")
    print("- long_summary: Issue description (max 1000 chars)")
    print("- action_items: LLM-generated actionable tasks")
    print("- score: Urgency score from 0.0 to 1.0")
