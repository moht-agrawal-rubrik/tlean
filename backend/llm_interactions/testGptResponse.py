import json
import os
from generateConversationSummarySlack2 import analyze_slack_conversation


def load_sample_data():
    """
    Load sample data from the JSON files.
    
    Returns:
        tuple: (target_message, previous_messages, next_messages, replies)
    """
    # Define file paths
    base_path = "/Users/mridulchandak/Desktop/hackathon/tlean/backend/slack"
    
    sample_messages_path = os.path.join(base_path, "sample_messages.json")
    sample_previous_path = os.path.join(base_path, "sample_previous_4_messages.json")
    sample_next_path = os.path.join(base_path, "sample_next_4_messages.json")
    sample_replies_path = os.path.join(base_path, "sample_replies.json")
    
    # Load target message (first match from sample_messages.json)
    with open(sample_messages_path, 'r') as f:
        messages_data = json.load(f)
        target_message = messages_data["messages"]["matches"][0]  # Take the first match
    
    # Load previous messages
    with open(sample_previous_path, 'r') as f:
        previous_data = json.load(f)
        previous_messages = previous_data["messages"]
    
    # Load next messages
    with open(sample_next_path, 'r') as f:
        next_data = json.load(f)
        next_messages = next_data["messages"]
    
    # Load replies
    with open(sample_replies_path, 'r') as f:
        replies_data = json.load(f)
        replies = replies_data["messages"]
    
    return target_message, previous_messages, next_messages, replies


def test_conversation_analysis():
    """
    Test the conversation analysis function with sample data.
    """
    print("Loading sample data...")
    
    try:
        # Load the sample data
        target_message, previous_messages, next_messages, replies = load_sample_data()
        
        print(f"Loaded data:")
        print(f"- Target message: {target_message.get('text', 'N/A')}")
        print(f"- Previous messages: {len(previous_messages)} messages")
        print(f"- Next messages: {len(next_messages)} messages") 
        print(f"- Replies: {len(replies)} messages")
        print("\n" + "="*50)
        
        # Call the analysis function
        print("Analyzing conversation...")
        result = analyze_slack_conversation(
            target_message=target_message,
            previous_messages=previous_messages,
            next_messages=next_messages,
            replies=replies
        )
        
        print("\nAnalysis Result:")
        print("="*50)
        print(result)
        
        # Try to parse and pretty print the JSON result
        try:
            parsed_result = json.loads(result)
            print("\nParsed JSON Result:")
            print("="*50)
            print(json.dumps(parsed_result, indent=2))
            
            # Extract key insights
            print("\nKey Insights:")
            print("="*50)
            print(f"Has Pending Action Items: {parsed_result.get('has_pending_action_items', 'Unknown')}")
            print(f"Number of Action Items: {len(parsed_result.get('action_items', []))}")
            print(f"Problem Summary: {parsed_result.get('problem_summary', 'N/A')}")
            print(f"Conversation Status: {parsed_result.get('conversation_status', 'Unknown')}")
            
        except json.JSONDecodeError:
            print("Note: Result is not valid JSON, displaying as text above.")
            
    except FileNotFoundError as e:
        print(f"Error: Could not find sample file - {e}")
    except KeyError as e:
        print(f"Error: Missing expected key in JSON data - {e}")
    except Exception as e:
        print(f"Error: {e}")


def main():
    """
    Main function to run the test.
    """
    print("Testing Slack Conversation Analysis")
    print("="*50)
    test_conversation_analysis()


if __name__ == "__main__":
    main()
