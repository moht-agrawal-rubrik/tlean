"""
Example usage of the GitHub candidate generator package.

This demonstrates how to use the github processing functions directly.
"""

import json
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from github_candidate_generator import GitHubCandidateGenerator
from pr_processor import process_github_pr_data


def example_basic_usage():
    """Example of basic usage with the GitHub package."""
    print("🚀 GitHub Package Usage Example")
    print("=" * 50)
    
    # Example 1: Process raw PR data directly
    print("\n📋 Example 1: Processing raw PR data")
    print("-" * 30)
    
    # Load sample data
    try:
        with open('result.json', 'r') as f:
            test_data = json.load(f)
        
        # Get the first PR's raw data
        raw_pr_data = test_data[0]['raw_data']
        
        # Process it using the package function
        processed = process_github_pr_data(raw_pr_data)
        
        print(f"✅ Processed PR: {processed['title']}")
        print(f"📊 Score: {processed['score']:.3f}")
        print(f"📝 Action Items: {len(processed['action_items'])}")
        for i, item in enumerate(processed['action_items'], 1):
            print(f"   {i}. {item}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Example 2: Using GitHubCandidateGenerator
    print("\n📋 Example 2: Using GitHubCandidateGenerator")
    print("-" * 30)
    
    try:
        # Initialize with dummy token for testing
        generator = GitHubCandidateGenerator("dummy_token")
        
        # Process the same raw data
        result = generator.process_with_llm(raw_pr_data)
        
        print(f"✅ Generated candidate: {result['candidate_id']}")
        print(f"📊 Score: {result['processed_data']['score']:.3f}")
        print(f"🔗 Link: {result['processed_data']['link']}")
        
    except Exception as e:
        print(f"❌ Error: {e}")


def example_batch_processing():
    """Example of processing multiple PRs."""
    print("\n📋 Example 3: Batch Processing")
    print("-" * 30)
    
    try:
        with open('result.json', 'r') as f:
            test_data = json.load(f)
        
        processed_candidates = []
        
        for item in test_data:
            raw_pr_data = item.get('raw_data', {})
            if raw_pr_data:
                processed = process_github_pr_data(raw_pr_data)
                processed_candidates.append(processed)
        
        # Sort by score (highest first)
        processed_candidates.sort(key=lambda x: x['score'], reverse=True)
        
        print(f"✅ Processed {len(processed_candidates)} PRs")
        print("\n📊 Top 3 by urgency:")
        
        for i, candidate in enumerate(processed_candidates[:3], 1):
            print(f"   {i}. {candidate['title'][:50]}...")
            print(f"      Score: {candidate['score']:.3f}")
            print(f"      Actions: {len(candidate['action_items'])}")
        
        # Save results
        with open('example_output.json', 'w') as f:
            json.dump(processed_candidates, f, indent=2)
        
        print(f"\n💾 Saved results to example_output.json")
        
    except Exception as e:
        print(f"❌ Error: {e}")


def example_filtering():
    """Example of filtering candidates by score."""
    print("\n📋 Example 4: Filtering by Score")
    print("-" * 30)
    
    try:
        with open('result.json', 'r') as f:
            test_data = json.load(f)
        
        all_candidates = []
        for item in test_data:
            raw_pr_data = item.get('raw_data', {})
            if raw_pr_data:
                processed = process_github_pr_data(raw_pr_data)
                all_candidates.append(processed)
        
        # Filter by different score thresholds
        high_priority = [c for c in all_candidates if c['score'] >= 0.5]
        medium_priority = [c for c in all_candidates if 0.3 <= c['score'] < 0.5]
        low_priority = [c for c in all_candidates if c['score'] < 0.3]
        
        print(f"📊 Priority Distribution:")
        print(f"   🔴 High (≥0.5): {len(high_priority)} PRs")
        print(f"   🟡 Medium (0.3-0.5): {len(medium_priority)} PRs")
        print(f"   🟢 Low (<0.3): {len(low_priority)} PRs")
        
        if high_priority:
            print(f"\n🔴 High Priority PRs:")
            for candidate in high_priority:
                print(f"   • {candidate['title'][:60]}... (Score: {candidate['score']:.3f})")
        
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    # Run all examples
    example_basic_usage()
    example_batch_processing()
    example_filtering()
    
    print("\n🎉 Examples completed!")
    print("\nNext steps:")
    print("1. Check the github/ folder for more detailed examples")
    print("2. Run 'cd github && python github_processor_demo.py' for full demo")
    print("3. See github/README.md for complete documentation")
