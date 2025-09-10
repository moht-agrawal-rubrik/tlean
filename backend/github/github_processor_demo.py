"""
Demo script showing the complete GitHub PR processing functionality.
This demonstrates the integration of all components according to guidelines.md.
"""

import json
import os
import sys
from typing import List, Dict, Any
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from pr_processor import process_github_pr_data


def process_github_candidates(raw_data_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Process a list of GitHub PR candidates into the required format.
    
    Args:
        raw_data_list: List of raw GitHub PR data (as from result.json)
        
    Returns:
        List of processed candidates in guidelines.md format
    """
    processed_candidates = []
    
    for item in raw_data_list:
        try:
            # Extract raw PR data
            if 'raw_data' in item:
                raw_pr_data = item['raw_data']
            else:
                # Assume the item itself is the raw data
                raw_pr_data = item
            
            # Process the PR data
            processed_candidate = process_github_pr_data(raw_pr_data)
            processed_candidates.append(processed_candidate)
            
        except Exception as e:
            print(f"Warning: Failed to process PR candidate: {e}")
            continue
    
    return processed_candidates


def rank_candidates(candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Rank candidates by urgency score in descending order.
    
    Args:
        candidates: List of processed candidates
        
    Returns:
        Sorted list of candidates (highest urgency first)
    """
    return sorted(candidates, key=lambda x: x.get('score', 0), reverse=True)


def filter_candidates_by_score(candidates: List[Dict[str, Any]], 
                              min_score: float = 0.3) -> List[Dict[str, Any]]:
    """
    Filter candidates by minimum urgency score.
    
    Args:
        candidates: List of processed candidates
        min_score: Minimum score threshold
        
    Returns:
        Filtered list of candidates
    """
    return [c for c in candidates if c.get('score', 0) >= min_score]


def display_candidates(candidates: List[Dict[str, Any]], title: str = "Candidates"):
    """Display candidates in a formatted way."""
    print(f"\n📋 {title}")
    print("=" * 60)
    
    if not candidates:
        print("No candidates found.")
        return
    
    for i, candidate in enumerate(candidates, 1):
        score = candidate.get('score', 0)
        title = candidate.get('title', 'Unknown')
        action_items = candidate.get('action_items', [])
        
        # Determine urgency level
        if score < 0.3:
            urgency = "🟢 Low"
        elif score < 0.6:
            urgency = "🟡 Medium"
        elif score < 0.8:
            urgency = "🟠 High"
        else:
            urgency = "🔴 Critical"
        
        print(f"\n{i}. {title}")
        print(f"   Score: {score:.3f} ({urgency})")
        print(f"   Link: {candidate.get('link', 'N/A')}")
        print(f"   Timestamp: {candidate.get('timestamp', 'N/A')}")
        
        if action_items:
            print(f"   Action Items:")
            for item in action_items:
                print(f"     • {item}")
        else:
            print(f"   Action Items: None")


def demo_complete_workflow():
    """Demonstrate the complete workflow from raw data to ranked candidates."""
    print("🚀 GitHub Candidate Generator Demo")
    print("=" * 60)
    
    # Load test data
    try:
        with open('result.json', 'r') as f:
            raw_data = json.load(f)
        print(f"✅ Loaded {len(raw_data)} raw PR records")
    except FileNotFoundError:
        print("❌ Error: result.json not found")
        return
    except json.JSONDecodeError as e:
        print(f"❌ Error parsing result.json: {e}")
        return
    
    # Process candidates
    print("\n🔄 Processing candidates...")
    processed_candidates = process_github_candidates(raw_data)
    print(f"✅ Successfully processed {len(processed_candidates)} candidates")
    
    # Display all candidates
    display_candidates(processed_candidates, "All Processed Candidates")
    
    # Rank candidates
    print("\n📊 Ranking candidates by urgency...")
    ranked_candidates = rank_candidates(processed_candidates)
    display_candidates(ranked_candidates, "Ranked Candidates (by urgency)")
    
    # Filter high-priority candidates
    print("\n🎯 Filtering high-priority candidates (score >= 0.4)...")
    high_priority = filter_candidates_by_score(ranked_candidates, min_score=0.4)
    display_candidates(high_priority, "High-Priority Candidates")
    
    # Show final output format
    print("\n📄 Final JSON Output (Guidelines.md Format):")
    print("-" * 50)
    print(json.dumps(ranked_candidates, indent=2))
    
    # Summary statistics
    print(f"\n📈 Summary Statistics:")
    print(f"   Total candidates: {len(processed_candidates)}")
    print(f"   High priority (≥0.4): {len([c for c in processed_candidates if c.get('score', 0) >= 0.4])}")
    print(f"   Medium priority (0.3-0.4): {len([c for c in processed_candidates if 0.3 <= c.get('score', 0) < 0.4])}")
    print(f"   Low priority (<0.3): {len([c for c in processed_candidates if c.get('score', 0) < 0.3])}")
    
    # Action items summary
    all_action_items = []
    for candidate in processed_candidates:
        all_action_items.extend(candidate.get('action_items', []))
    
    print(f"   Total action items: {len(all_action_items)}")
    
    # Most common action items
    from collections import Counter
    if all_action_items:
        common_actions = Counter(all_action_items).most_common(3)
        print(f"   Most common actions:")
        for action, count in common_actions:
            print(f"     • {action} ({count}x)")


def create_sample_output():
    """Create a sample output file in the correct format."""
    try:
        with open('result.json', 'r') as f:
            raw_data = json.load(f)
        
        # Process the data
        processed_candidates = process_github_candidates(raw_data)
        ranked_candidates = rank_candidates(processed_candidates)
        
        # Save to output file
        with open('processed_candidates.json', 'w') as f:
            json.dump(ranked_candidates, f, indent=2)
        
        print("✅ Created processed_candidates.json with the final output")
        
    except Exception as e:
        print(f"❌ Error creating sample output: {e}")


if __name__ == "__main__":
    # Run the complete demo
    demo_complete_workflow()
    
    # Create sample output file
    print("\n" + "=" * 60)
    create_sample_output()
