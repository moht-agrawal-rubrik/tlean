"""
Integration test to verify the complete GitHub candidate generation workflow.
"""

import json
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from github_candidate_generator import GitHubCandidateGenerator


def test_integration():
    """Test the complete integration with the updated GitHubCandidateGenerator."""
    print("🧪 Integration Test - GitHub Candidate Generator")
    print("=" * 60)
    
    # Initialize the generator
    github_token = os.getenv('GITHUB_TOKEN')
    generator = GitHubCandidateGenerator(github_token)
    
    # Load test data
    try:
        with open('result.json', 'r') as f:
            test_data = json.load(f)
        print(f"✅ Loaded {len(test_data)} test records")
    except FileNotFoundError:
        print("❌ Error: result.json not found")
        return
    
    # Test processing with the updated generator
    print("\n🔄 Testing updated GitHubCandidateGenerator...")
    
    for i, item in enumerate(test_data):
        raw_pr_data = item.get('raw_data', {})
        if not raw_pr_data:
            continue
            
        print(f"\n📋 Processing PR #{i+1}: {raw_pr_data.get('pr_title', 'Unknown')}")
        
        try:
            # Process with the updated method
            result = generator.process_with_llm(raw_pr_data)
            
            # Validate the result structure
            print("✅ Processing successful")
            
            # Check that we have both old and new format
            assert 'source' in result
            assert 'candidate_id' in result
            assert 'raw_data' in result
            assert 'processed_data' in result
            
            processed = result['processed_data']
            
            # Validate guidelines.md format
            required_fields = ['source', 'link', 'timestamp', 'title', 'long_summary', 'action_items', 'score']
            for field in required_fields:
                assert field in processed, f"Missing field: {field}"
            
            print(f"   📊 Score: {processed['score']:.3f}")
            print(f"   📝 Action Items: {len(processed['action_items'])}")
            print(f"   🔗 Link: {processed['link']}")
            
            # Show action items
            for j, item in enumerate(processed['action_items'], 1):
                print(f"      {j}. {item}")
                
        except Exception as e:
            print(f"❌ Processing failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    print("\n✅ All integration tests passed!")
    return True


def test_guidelines_format_compliance():
    """Test that output strictly follows guidelines.md format."""
    print("\n🔍 Testing Guidelines.md Format Compliance")
    print("-" * 50)

    # Load test data
    with open('result.json', 'r') as f:
        test_data = json.load(f)

    # Use a dummy token for testing (we're not making API calls)
    generator = GitHubCandidateGenerator("dummy_token")
    
    # Process one PR and extract the guidelines format
    raw_pr_data = test_data[0]['raw_data']
    result = generator.process_with_llm(raw_pr_data)
    guidelines_format = result['processed_data']
    
    # Validate exact format
    expected_schema = {
        "source": str,
        "link": str,
        "timestamp": str,
        "title": str,
        "long_summary": str,
        "action_items": list,
        "score": (int, float)
    }
    
    print("📋 Schema Validation:")
    for field, expected_type in expected_schema.items():
        if field not in guidelines_format:
            print(f"❌ Missing field: {field}")
            return False
        
        actual_type = type(guidelines_format[field])
        if not isinstance(guidelines_format[field], expected_type):
            print(f"❌ Wrong type for {field}: expected {expected_type}, got {actual_type}")
            return False
        
        print(f"✅ {field}: {actual_type.__name__}")
    
    # Validate constraints
    print("\n📏 Constraint Validation:")
    
    # Title length
    title_len = len(guidelines_format['title'])
    if title_len <= 200:
        print(f"✅ Title length: {title_len} chars (≤ 200)")
    else:
        print(f"❌ Title too long: {title_len} chars (> 200)")
        return False
    
    # Summary length
    summary_len = len(guidelines_format['long_summary'])
    if summary_len <= 1000:
        print(f"✅ Summary length: {summary_len} chars (≤ 1000)")
    else:
        print(f"❌ Summary too long: {summary_len} chars (> 1000)")
        return False
    
    # Score range
    score = guidelines_format['score']
    if 0.0 <= score <= 1.0:
        print(f"✅ Score range: {score:.3f} (0.0-1.0)")
    else:
        print(f"❌ Score out of range: {score} (not 0.0-1.0)")
        return False
    
    # Source value
    if guidelines_format['source'] == 'github':
        print(f"✅ Source: {guidelines_format['source']}")
    else:
        print(f"❌ Wrong source: {guidelines_format['source']} (expected 'github')")
        return False
    
    # Timestamp format (basic check)
    timestamp = guidelines_format['timestamp']
    if len(timestamp) == 19 and timestamp[10] == ' ':  # YYYY-MM-DD HH:MM:SS
        print(f"✅ Timestamp format: {timestamp}")
    else:
        print(f"❌ Wrong timestamp format: {timestamp}")
        return False
    
    print("\n✅ All format compliance tests passed!")
    return True


def create_final_demo_output():
    """Create a final demo output showing the complete workflow."""
    print("\n📄 Creating Final Demo Output")
    print("-" * 40)

    # Load and process all test data
    with open('result.json', 'r') as f:
        test_data = json.load(f)

    generator = GitHubCandidateGenerator("dummy_token")
    final_candidates = []
    
    for item in test_data:
        raw_pr_data = item.get('raw_data', {})
        if raw_pr_data:
            result = generator.process_with_llm(raw_pr_data)
            final_candidates.append(result['processed_data'])
    
    # Sort by score (highest first)
    final_candidates.sort(key=lambda x: x['score'], reverse=True)
    
    # Save final output
    with open('final_github_candidates.json', 'w') as f:
        json.dump(final_candidates, f, indent=2)
    
    print(f"✅ Created final_github_candidates.json with {len(final_candidates)} candidates")
    print(f"📊 Score range: {final_candidates[-1]['score']:.3f} - {final_candidates[0]['score']:.3f}")
    
    return final_candidates


if __name__ == "__main__":
    # Run all tests
    success = True
    
    success &= test_integration()
    success &= test_guidelines_format_compliance()
    
    if success:
        create_final_demo_output()
        print("\n🎉 All tests passed! Integration complete.")
    else:
        print("\n❌ Some tests failed. Please check the output above.")
