"""
Test script to validate the PR processor with existing result.json data.
"""

import json
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from pr_processor import process_github_pr_data, PRProcessor


def load_test_data():
    """Load the test data from result.json."""
    try:
        # Look for result.json in current directory
        with open('result.json', 'r') as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        print("Error: result.json not found")
        return None
    except json.JSONDecodeError as e:
        print(f"Error parsing result.json: {e}")
        return None


def test_pr_processor():
    """Test the PR processor with the sample data."""
    print("🧪 Testing PR Processor")
    print("=" * 50)
    
    # Load test data
    test_data = load_test_data()
    if not test_data:
        return
    
    # Extract the raw PR data (assuming it's the first item in the list)
    if isinstance(test_data, list) and len(test_data) > 0:
        raw_pr_data = test_data[0].get('raw_data', {})
    else:
        print("Error: Unexpected data format in result.json")
        return
    
    if not raw_pr_data:
        print("Error: No raw_data found in test data")
        return
    
    print(f"📋 Processing PR: {raw_pr_data.get('pr_title', 'Unknown')}")
    print()
    
    # Process the data
    try:
        processed_data = process_github_pr_data(raw_pr_data)
        
        # Display results
        print("✅ Processing successful!")
        print()
        print("📊 PROCESSED OUTPUT:")
        print("-" * 30)
        print(json.dumps(processed_data, indent=2))
        
        # Validate format
        print()
        print("🔍 FORMAT VALIDATION:")
        print("-" * 30)
        validate_format(processed_data)
        
        # Analyze action items
        print()
        print("📝 ACTION ITEMS ANALYSIS:")
        print("-" * 30)
        analyze_action_items(raw_pr_data, processed_data)
        
        # Analyze scoring
        print()
        print("📈 SCORING ANALYSIS:")
        print("-" * 30)
        analyze_scoring(raw_pr_data, processed_data)
        
    except Exception as e:
        print(f"❌ Processing failed: {e}")
        import traceback
        traceback.print_exc()


def validate_format(processed_data):
    """Validate that the processed data matches the required format."""
    required_fields = ['source', 'link', 'timestamp', 'title', 'long_summary', 'action_items', 'score']
    
    for field in required_fields:
        if field not in processed_data:
            print(f"❌ Missing required field: {field}")
        else:
            print(f"✅ {field}: present")
    
    # Validate field types and constraints
    if 'source' in processed_data:
        if processed_data['source'] != 'github':
            print(f"⚠️  Source should be 'github', got: {processed_data['source']}")
    
    if 'title' in processed_data:
        title_len = len(processed_data['title'])
        if title_len > 200:
            print(f"⚠️  Title too long: {title_len} chars (max 200)")
        else:
            print(f"✅ Title length: {title_len} chars")
    
    if 'long_summary' in processed_data:
        summary_len = len(processed_data['long_summary'])
        if summary_len > 1000:
            print(f"⚠️  Summary too long: {summary_len} chars (max 1000)")
        else:
            print(f"✅ Summary length: {summary_len} chars")
    
    if 'action_items' in processed_data:
        if not isinstance(processed_data['action_items'], list):
            print(f"⚠️  Action items should be a list")
        else:
            print(f"✅ Action items: {len(processed_data['action_items'])} items")
    
    if 'score' in processed_data:
        score = processed_data['score']
        if not isinstance(score, (int, float)) or score < 0 or score > 1:
            print(f"⚠️  Score should be float 0.0-1.0, got: {score}")
        else:
            print(f"✅ Score: {score:.3f}")


def analyze_action_items(raw_data, processed_data):
    """Analyze the action items generation."""
    comments = raw_data.get('comments', {})
    global_comments = comments.get('global_comments', [])
    inline_comments = comments.get('inline_comments', [])
    
    # Count bot vs human comments
    processor = PRProcessor()
    
    human_global = [c for c in global_comments if not processor._is_bot_comment(c)]
    human_inline = [c for c in inline_comments if not processor._is_bot_comment(c)]
    bot_global = [c for c in global_comments if processor._is_bot_comment(c)]
    bot_inline = [c for c in inline_comments if processor._is_bot_comment(c)]
    
    print(f"📊 Comment Analysis:")
    print(f"   Global comments: {len(global_comments)} total ({len(human_global)} human, {len(bot_global)} bot)")
    print(f"   Inline comments: {len(inline_comments)} total ({len(human_inline)} human, {len(bot_inline)} bot)")
    
    # Show bot accounts detected
    bot_authors = set()
    for comment in bot_global + bot_inline:
        bot_authors.add(comment.get('author', 'Unknown'))
    
    if bot_authors:
        print(f"🤖 Bot accounts filtered: {', '.join(sorted(bot_authors))}")
    
    # Show action items generated
    action_items = processed_data.get('action_items', [])
    print(f"📝 Generated {len(action_items)} action items:")
    for i, item in enumerate(action_items, 1):
        print(f"   {i}. {item}")


def analyze_scoring(raw_data, processed_data):
    """Analyze the scoring calculation."""
    processor = PRProcessor()
    metadata = raw_data.get('metadata', {})
    
    # Calculate individual factors
    time_factor = processor._calculate_time_factor(metadata)
    reviewer_factor = processor._calculate_reviewer_factor(metadata, raw_data.get('comments', {}))
    comment_factor = processor._calculate_comment_factor(raw_data.get('comments', {}), metadata.get('author', ''))
    
    final_score = processed_data.get('score', 0)
    
    print(f"📈 Score Breakdown:")
    print(f"   Base score: 0.1")
    print(f"   Time factor: {time_factor:.3f}")
    print(f"   Reviewer factor: {reviewer_factor:.3f}")
    print(f"   Comment factor: {comment_factor:.3f}")
    print(f"   Final score: {final_score:.3f}")
    
    # Interpret urgency level
    if final_score < 0.3:
        urgency = "Low"
    elif final_score < 0.6:
        urgency = "Medium"
    elif final_score < 0.8:
        urgency = "High"
    else:
        urgency = "Critical"
    
    print(f"   Urgency level: {urgency}")
    
    # Show key metrics
    print(f"📊 Key Metrics:")
    print(f"   PR age: {metadata.get('created_at', 'Unknown')}")
    print(f"   Last update: {metadata.get('updated_at', 'Unknown')}")
    print(f"   Reviewers: {len(metadata.get('reviewers', []))}")
    print(f"   Assignees: {len(metadata.get('assignees', []))}")
    print(f"   State: {metadata.get('state', 'Unknown')}")


if __name__ == "__main__":
    test_pr_processor()
