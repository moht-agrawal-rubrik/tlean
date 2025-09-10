import os
import re
from jira import JIRA
from dotenv import load_dotenv
import json
import requests # Needed for making raw HTTP requests to the internal Jira dev-status API
from datetime import datetime, timezone
from typing import List, Dict, Any
from openai import OpenAI

load_dotenv()

JIRA_SERVER = os.getenv("JIRA_SERVER")
USERNAME = os.getenv("USERNAME")
API_TOKEN = os.getenv("API_TOKEN")

# Initialize Jira connection
jira = JIRA(
    server=JIRA_SERVER or "",
    basic_auth=(USERNAME or "", API_TOKEN or "")
)

def get_full_markdown(key: str) -> tuple[str, str, str]:
    """
    Fetches a Jira issue by its key and formats its details into a Markdown string.
    It also returns the issue's summary and a pipe-separated, sorted string
    of its root cause labels.

    Args:
        key (str): The Jira issue key (e.g., "CDM-123").

    Returns:
        tuple[str, str, str]: A tuple containing:
            - str: Markdown formatted string of the Jira issue's details.
            - str: The issue's summary.
            - str: Pipe-separated, sorted string of root cause labels, or "Unclassified".
    """
    try:
        issue = jira.issue(key)
    except Exception as e:
        print(f"Error: Could not retrieve Jira issue {key}. Reason: {e}")
        # Return default values in case of error
        return f"Error: Could not retrieve Jira issue {key}.", "Error - Issue Not Found", "Unclassified"

    # Helper function to safely get attribute value from Jira objects
    def get_attribute_value(obj, attr_name):
        # Use getattr to safely access attributes, returning None if not found
        value = getattr(obj, attr_name, None)

        # Handle specific complex fields
        if attr_name == 'customfield_11200': # Development Panel (Pull Request info summary)
            if value:
                try:
                    # The value is a string representation of a JSON object.
                    # Replace single quotes with double quotes, and Python booleans/None with JS equivalents.
                    parsed_value_str = str(value).replace("'", "\"").replace("True", "true").replace("False", "false").replace("None", "null")
                    parsed_value = json.loads(parsed_value_str)
                    summary = parsed_value.get('json', {}).get('cachedValue', {}).get('summary', {}).get('pullrequest', {}).get('overall', {})
                    if summary:
                        return f"Pull Request Summary: State={summary.get('state', 'N/A')}, Count={summary.get('count', 'N/A')}, LastUpdated={summary.get('lastUpdated', 'N/A')}, DataType={summary.get('dataType', 'N/A')}"
                    return str(value) # Fallback to raw string if parsing fails or no summary
                except (json.JSONDecodeError, AttributeError, KeyError):
                    return f"Raw Development Info (Parsing Error): {str(value)}"
            return "None"
        elif isinstance(value, list):
            # Handle lists of Jira objects (Components, Versions) by joining their names
            if attr_name in ['components', 'versions', 'fixVersions', 'customfield_17427']:
                return ", ".join([item.name for item in value if hasattr(item, 'name')])
            # Handle lists of strings (Labels, Salesforce Ticket, other generic string lists)
            elif attr_name in ['labels', 'customfield_12613']:
                return ", ".join(value)
            # Special handling for root_cause_labels: sort and pipe-separate
            elif attr_name == 'customfield_13328':
                if value: # Check if the list is not empty
                    sorted_labels = sorted(value)
                    return "|".join(sorted_labels)
                return "Unclassified" # Return "Unclassified" for empty/null root cause labels list
            else:
                return str(value) if value else "None"
        elif hasattr(value, 'name'): # For objects with a 'name' attribute (e.g., IssueType, Priority, Status, Resolution)
            return value.name
        elif hasattr(value, 'displayName'): # For User objects
            return value.displayName
        elif hasattr(value, 'value'): # For CustomFieldOption objects (e.g., Yes/No, TBD)
            return value.value
        # Default case for string, int, None, etc.
        return str(value) if value is not None and value != '' else "None"


    # --- Extract core values to be returned ---
    issue_summary = issue.fields.summary if issue.fields.summary else "No Summary"

    # Safely get customfield_13328. If it doesn't exist, getattr returns None.
    root_cause_labels_raw = getattr(issue.fields, 'customfield_13328', None)
    
    if root_cause_labels_raw and isinstance(root_cause_labels_raw, list) and len(root_cause_labels_raw) > 0:
        sorted_labels = sorted(root_cause_labels_raw)
        root_cause_labels_formatted = "|".join(sorted_labels)
    else:
        root_cause_labels_formatted = "Unclassified" # Default when attribute is missing, None, or empty list

    # --- Attempt to fetch Development Panel details via internal Atlassian API ---
    github_pull_requests_details = []
    base_url = JIRA_SERVER.rstrip('/')
    dev_status_url = f"{base_url}/rest/dev-status/1.0/issue/detail?issueId={issue.id}&applicationType=github&dataType=pullrequest"

    try:
        response = requests.get(
            dev_status_url,
            auth=(USERNAME, API_TOKEN),
            headers={'Accept': 'application/json'}
        )
        response.raise_for_status()
        dev_data = response.json()

        if dev_data and 'detail' in dev_data and dev_data['detail']:
            for detail_item in dev_data['detail']:
                if 'pullRequests' in detail_item:
                    for pr in detail_item['pullRequests']:
                        github_pull_requests_details.append({
                            "id": pr.get('id', 'N/A'),
                            "name": pr.get('name', 'N/A'),
                            "url": pr.get('url', 'N/A'),
                            "status": pr.get('status', {}).get('displayName', 'N/A') if pr.get('status') else 'N/A',
                            "lastUpdated": pr.get('updateSequenceId', 'N/A'),
                            "author": pr.get('author', {}).get('name', 'N/A'),
                            "sourceBranch": pr.get('source', {}).get('branch', 'N/A'),
                            "destinationBranch": pr.get('destination', {}).get('branch', 'N/A'),
                            "commentCount": pr.get('commentCount', 0)
                        })
    except requests.exceptions.RequestException as e:
        print(f"Warning: Could not fetch development details for {key} from Jira's internal API. Error: {e}")
    except json.JSONDecodeError as e:
        print(f"Warning: Could not parse development details JSON from Jira's internal API for {key}. Error: {e}")
    
    # --- Constructing the Metadata Section ---
    metadata = {
        "Issue Type": get_attribute_value(issue.fields, 'issuetype'),
        "Status": get_attribute_value(issue.fields, 'status'),
        "Resolution": get_attribute_value(issue.fields, 'resolution'),
        "Priority": get_attribute_value(issue.fields, 'priority'),
        "Severity": get_attribute_value(issue.fields, 'customfield_12300'),
        "Urgency": get_attribute_value(issue.fields, 'customfield_12509'),
        "Assignee": get_attribute_value(issue.fields, 'assignee'),
        "Reporter": get_attribute_value(issue.fields, 'reporter'),
        "Components": get_attribute_value(issue.fields, 'components'),
        "Labels": get_attribute_value(issue.fields, 'labels'),
        "Root Cause Labels": get_attribute_value(issue.fields, 'customfield_13328'), # Will be pipe-separated due to get_attribute_value logic
        "Created": get_attribute_value(issue.fields, 'created'),
        "Updated": get_attribute_value(issue.fields, 'updated'),
        "Resolved Date": get_attribute_value(issue.fields, 'resolutiondate'),
        "Due Date": get_attribute_value(issue.fields, 'duedate'),
        "Affects Versions": get_attribute_value(issue.fields, 'versions'),
        "Fix Versions": get_attribute_value(issue.fields, 'fixVersions'),
        "Salesforce Ticket": get_attribute_value(issue.fields, 'customfield_12613'),
        "Regression": get_attribute_value(issue.fields, 'customfield_11501'),
        "Sprint": get_attribute_value(issue.fields, 'customfield_11400'),
        "Account": get_attribute_value(issue.fields, 'customfield_12640'),
        "Cluster ID": get_attribute_value(issue.fields, 'customfield_12917'),
        "Additional Cluster ID": get_attribute_value(issue.fields, 'customfield_14610'),
        "Component Manager": get_attribute_value(issue.fields, 'customfield_12713'),
        "Customer Case Owner": get_attribute_value(issue.fields, 'customfield_12931'),
        "Customer Case Manager": get_attribute_value(issue.fields, 'customfield_13440'),
        "Assist Request Owner": get_attribute_value(issue.fields, 'customfield_14593'),
        "Where Ideally Found": get_attribute_value(issue.fields, 'customfield_11600'),
        "Approving Manager": get_attribute_value(issue.fields, 'customfield_11900'),
        "Component Change Counter": get_attribute_value(issue.fields, 'customfield_11901'),
        "QA Contact": get_attribute_value(issue.fields, 'customfield_11902'),
        "Release Notes Candidate": get_attribute_value(issue.fields, 'customfield_12924'),
        "TestRail: Cases": get_attribute_value(issue.fields, 'customfield_12000'),
        "TestRail: Runs": get_attribute_value(issue.fields, 'customfield_12100'),
        "Was Ever P0": get_attribute_value(issue.fields, 'customfield_11000'),
        "Story Points": get_attribute_value(issue.fields, 'customfield_12615'),
        "Development Panel Summary": get_attribute_value(issue.fields, 'customfield_11200'),
        "Issue Links Present": "Yes" if issue.fields.issuelinks else "No",
        "Impact Level": get_attribute_value(issue.fields, 'customfield_14916'),
        "Estimated Effort (customfield_12947)": get_attribute_value(issue.fields, 'customfield_12947'),
        "Custom Field 13037": get_attribute_value(issue.fields, 'customfield_13037'),
        "Custom Field 13252": get_attribute_value(issue.fields, 'customfield_13252'),
        "Design Doc Reviews Status": get_attribute_value(issue.fields, 'customfield_12914'),
        "Environment Type": get_attribute_value(issue.fields, 'customfield_13444'),
        "SLA Status": get_attribute_value(issue.fields, 'customfield_13075'),
        "Known Issue/Workaround": get_attribute_value(issue.fields, 'customfield_13246'),
        "Is Fixed": get_attribute_value(issue.fields, 'customfield_12988'),
        "Creator": get_attribute_value(issue.fields, 'creator'),
        "Environment": get_attribute_value(issue.fields, 'environment'),
        "Time Spent": get_attribute_value(issue.fields, 'timespent'),
        "Original Estimate": get_attribute_value(issue.fields, 'timeoriginalestimate'),
        "Time Tracking": get_attribute_value(issue.fields, 'timetracking'),
        "Work Ratio": get_attribute_value(issue.fields, 'workratio'),
    }

    markdown_output = "---\n"
    for label, value in metadata.items():
        markdown_output += f"{label}: {value}\n"
    markdown_output += "---\n\n"

    markdown_output += f"# {issue.key} - {issue_summary}\n\n"

    markdown_output += "## Description\n\n"
    if issue.fields.description:
        markdown_output += issue.fields.description + "\n\n"
    else:
        markdown_output += "No description provided.\n\n"

    # Add specific custom field descriptions that seem like part of the main narrative description
    description_fields = {
        "Outward Symptoms": 'customfield_12935',
        "Defect Initiating Failure Sequence": 'customfield_12936',
        "Resolution Summary": 'customfield_12937',
        "Fixed Issues Notes": 'customfield_12938',
        "Summary of Issue Observed": 'customfield_12709',
        "Narrative of Events": 'customfield_12710',
        "Could We Have Caught This Earlier?": 'customfield_12711',
        "Root Cause Description": 'customfield_12712',
        "Mitigation Status Update Note": 'customfield_14595',
        "Action Results/Explanation": 'customfield_12998',
        "Jarvis Issues Note": 'customfield_13463',
        "Kaustubh -> Yash Notes": 'customfield_14590',
        "CLA Template Recommendation": 'customfield_14781',
        "Resolution Guidelines": 'customfield_14918',
        "Score Guidelines": 'customfield_16216',
        "SFDC Case Comment Note": 'customfield_13350',
        "CLA Action JIRA Summary": 'customfield_12996',
        "Temp Fix/Workaround (customfield_11503)": 'customfield_11503',
        "Customer Advisory": 'customfield_13246',
        "TechOps Components & Team Info": 'customfield_12894',
        "Priority, Severity, Urgency Update Note": 'customfield_12789',
        "Description Field Guidance": 'customfield_12790',
        "Accessing Dev Info": 'customfield_12895',
    }

    for label, field_id in description_fields.items():
        content = get_attribute_value(issue.fields, field_id)
        if content and content != "None" and not content.startswith('{color:blue}') and not content.startswith('|{color:'):
            markdown_output += f"### {label}\n\n{content}\n\n"
        elif content and content != "None":
            markdown_output += f"**{label} Prompt:** {content}\n\n"

    # Add Development Details if found from Jira's internal API
    if github_pull_requests_details:
        markdown_output += "## Development Details (Linked Pull Requests from Jira Integration)\n\n"
        for pr_data in github_pull_requests_details:
            markdown_output += f"- **PR ID:** {pr_data['id']}\n"
            markdown_output += f"  - **Title:** {pr_data['name']}\n"
            markdown_output += f"  - **URL:** {pr_data['url']}\n"
            markdown_output += f"  - **Status:** {pr_data['status']}\n"
            markdown_output += f"  - **Author:** {pr_data['author']}\n"
            markdown_output += f"  - **Source Branch:** {pr_data['sourceBranch']}\n"
            markdown_output += f"  - **Destination Branch:** {pr_data['destinationBranch']}\n"
            markdown_output += f"  - **Comment Count:** {pr_data['commentCount']}\n"
            markdown_output += "\n"
    else:
        markdown_output += "## Development Details\n\nNo linked GitHub Pull Request details found via Jira's internal integration API.\n\n"


    markdown_output += "## Comments\n\n"
    comments = issue.fields.comment.comments
    if comments:
        for comment in comments:
            markdown_output += f"**{comment.author.displayName}** on {comment.created}:\n"
            markdown_output += f"{comment.body}\n\n"
    else:
        markdown_output += "No comments found.\n\n"

    # Return the markdown content, summary, and formatted root cause labels
    return markdown_output, issue_summary, root_cause_labels_formatted


def find_jira_keys_by_conditions() -> list[str]:
    """
    Finds Jira issue keys that satisfy the following conditions:
    - Assigned to current user
    - Status is open (not resolved or closed)
    - Limited to 10 results

    Returns:
        list[str]: A list of Jira issue keys that match the criteria.
    """
    # JQL for the conditions:
    # 1. Assigned to current user
    # 2. Status is open (not resolved, closed, done, etc.)
    jql_query = (
        'assignee = currentUser() AND status not in (Resolved, Closed, Done, "Won\'t Fix", Cancelled, Applied, Verified, "Feature Approved", "Conditionally Approved")'
    )

    matching_keys = []
    max_results = 10  # Limit to 10 issues total

    try:
        # Perform the JQL search with limit of 10 results
        # fields=['key'] ensures we only fetch the issue key, making the request lighter.
        issues = jira.search_issues(jql_query, startAt=0, maxResults=max_results, fields=['key'])

        for issue in issues:
            matching_keys.append(issue.key)

    except Exception as e:
        print(f"An error occurred during Jira search: {e}")
        # Depending on your error handling needs, you might want to re-raise the exception
        # or return an empty list/partial list.
        return [] # Return empty list on error for this example

    return matching_keys



# --- New Sanitization Helper Function ---
def sanitize_path_component(name: str, max_len: int = 250) -> str:
    """
    Sanitizes a string to be safe for use as a file or folder name.
    Replaces invalid characters with underscores and truncates to max_len.
    """
    # Define characters that are typically invalid in filenames across OS
    # This list covers Windows, macOS, and Linux common restrictions.
    invalid_chars_pattern = r'[<>:"/\\|?*\x00-\x1F]' # ASCII control characters (0x00-0x1F) also
    
    # Replace invalid characters with an underscore
    sanitized_name = re.sub(invalid_chars_pattern, '_', name)
    
    # Remove leading/trailing spaces and dots
    sanitized_name = sanitized_name.strip(' .')
    
    # Replace multiple underscores with a single underscore
    sanitized_name = re.sub(r'__+', '_', sanitized_name)
    
    # Limit length (e.g., for Windows MAX_PATH is ~260, but shorter is better)
    sanitized_name = sanitized_name[:max_len].strip()
    
    # Ensure it's not empty after sanitization
    if not sanitized_name:
        return "Unnamed_Component" # Fallback if sanitization makes it empty
        
    return sanitized_name


# --- Main Logic for Scraping and Saving ---
# def main():
#     base_dir = 'rba-jiras'
#     if not os.path.exists(base_dir):
#         os.mkdir(base_dir)
#         print(f"Created base directory: {base_dir}")

#     keys = find_jira_keys_by_conditions()
#     if not keys:
#         print("No Jira issues found matching the conditions.")
#         return

#     print(f"Found {len(keys)} matching Jira issues. Starting content generation...")
#     for i, key in enumerate(keys):
#         print(f"[{i+1}/{len(keys)}] Processing issue: {key}")
        
#         markdown_content, summary, root_cause_labels_str = get_full_markdown(key)
        
#         # Sanitize folder name
#         sanitized_folder_name = sanitize_path_component(root_cause_labels_str, max_len=50)
#         folder_path = os.path.join(base_dir, sanitized_folder_name)

#         # Create folder if it doesn't exist
#         if not os.path.exists(folder_path):
#             try:
#                 os.mkdir(folder_path)
#                 print(f"Created folder: {folder_path}")
#             except OSError as e:
#                 print(f"Error creating folder {folder_path}: {e}. Skipping this issue.")
#                 continue # Skip to next issue if folder creation fails

#         # Sanitize file name (summary part)
#         # Use the issue key as is, as it's typically safe.
#         sanitized_summary_for_filename = sanitize_path_component(summary, max_len=100) # Longer max_len for filename part
        
#         # Construct the full file name
#         file_name = f"[{key}] {sanitized_summary_for_filename}.md"
#         file_path = os.path.join(folder_path, file_name)

#         print(f'Writing {key} to {file_path}')
#         try:
#             with open(file_path, 'w', encoding='utf-8') as f: # Specify encoding for broad character support
#                 f.write(markdown_content)
#             print(f'Successfully wrote {file_name}')
#         except OSError as e:
#             print(f"Error writing file {file_path}: {e}")
#         except Exception as e:
#             print(f"An unexpected error occurred while writing {file_path}: {e}")

#     print("\nContent generation complete.")


# def main():
#     keys = find_jira_keys_by_conditions()
#     if not os.path.exists('rba-jiras'):
#         os.mkdir('rba-jiras')
#
#     for key in keys:
#         markdown, summary, root_cause_labels = get_full_markdown(key)
#         # create a folder called {root_cause_labels} inside 'rba-jiras'
#         if not os.path.exists(f'rba-jiras/{root_cause_labels}'):
#             os.mkdir(f'rba-jiras/{root_cause_labels}')
#
#         print(f'Writing {key} to {root_cause_labels}')
#         with open(f'rba-jiras/{root_cause_labels}/[{key}] {summary}.md', 'w') as f:
#             f.write(markdown)
#     pass

class JiraJSONProcessor:
    """
    A class to process JIRA issues and convert them to JSON format with LLM-generated action items and scoring.
    """

    def __init__(self):
        """Initialize the OpenAI client for LLM analysis."""
        self.openai_client = OpenAI(
            api_key=os.environ.get("OPENAI_API_KEY"),
            base_url="https://basecamp.stark.rubrik.com"
        )

    def _parse_jira_timestamp(self, timestamp_str: str) -> str:
        """
        Parse JIRA timestamp and convert to UTC format.

        Args:
            timestamp_str: JIRA timestamp string

        Returns:
            Formatted timestamp string in UTC (YYYY-MM-DD HH:MM:SS)
        """
        try:
            # JIRA timestamps are typically in format: 2024-01-15T10:30:45.000+0000
            if timestamp_str and timestamp_str != "None":
                # Remove timezone info and milliseconds for parsing
                clean_timestamp = timestamp_str.split('.')[0].replace('T', ' ')
                if '+' in clean_timestamp:
                    clean_timestamp = clean_timestamp.split('+')[0]
                elif 'Z' in clean_timestamp:
                    clean_timestamp = clean_timestamp.replace('Z', '')

                # Parse and format
                dt = datetime.strptime(clean_timestamp, '%Y-%m-%d %H:%M:%S')
                return dt.strftime('%Y-%m-%d %H:%M:%S')
        except Exception as e:
            print(f"Warning: Could not parse timestamp '{timestamp_str}': {e}")

        # Fallback to current time if parsing fails
        return datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')

    def _generate_short_summary(self, issue_data: Dict[str, Any]) -> str:
        """
        Use LLM to generate a short summary of the JIRA issue including status.

        Args:
            issue_data: Dictionary containing JIRA issue information

        Returns:
            Short summary string (max 1000 characters)
        """
        try:
            # Create system prompt for summary generation
            system_prompt = """You are an expert JIRA issue summarizer. Generate concise, informative summaries.

SUMMARY RULES:
- Maximum 1000 characters total
- Include the current status prominently
- Focus on the core problem/task and current state
- Include key context like customer impact, priority, or technical details
- Use clear, professional language
- Structure: [Status] Brief description of the issue/task and current situation

EXAMPLES:
- "[In Progress] Customer experiencing 504 timeouts after GraphQL migration affecting 50+ hosts. API calls succeed but take >10 minutes causing automation failures."
- "[Resolved] Implemented secondary host registration API with UI integration. All testing completed and feature deployed to production."
- "[Open] Need to add performance metrics to Tableau dashboard for RBS deployment feature. Waiting for #turbo-team coordination."

Respond with ONLY the summary text (no JSON, no quotes, just the summary)."""

            # Create user prompt with issue data
            user_prompt = f"""Please generate a short summary for this JIRA issue:

Issue Key: {issue_data.get('key', 'N/A')}
Summary: {issue_data.get('summary', 'N/A')}
Status: {issue_data.get('status', 'N/A')}
Priority: {issue_data.get('priority', 'N/A')}
Issue Type: {issue_data.get('issue_type', 'N/A')}
Assignee: {issue_data.get('assignee', 'N/A')}
Created: {issue_data.get('created', 'N/A')}
Updated: {issue_data.get('updated', 'N/A')}

Description: {issue_data.get('description', 'N/A')[:1500]}...

Recent Comments: {issue_data.get('recent_comments', 'N/A')[:500]}..."""

            # Call OpenAI API
            response = self.openai_client.chat.completions.create(
                model="gpt-4.1",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                max_tokens=300  # Allow more tokens for summary generation
            )

            # Get the summary
            summary = response.choices[0].message.content.strip()

            # Ensure it's within the character limit
            if len(summary) > 1000:
                summary = summary[:997] + "..."

            return summary

        except Exception as e:
            print(f"Warning: LLM summary generation failed for issue {issue_data.get('key', 'unknown')}: {e}")
            # Fallback to status + description
            status = issue_data.get('status', 'Unknown')
            description = issue_data.get('description', 'No description provided.')
            fallback_summary = f"[{status}] {description}"
            if len(fallback_summary) > 1000:
                fallback_summary = fallback_summary[:997] + "..."
            return fallback_summary

    def _generate_action_items_and_score(self, issue_data: Dict[str, Any]) -> tuple[List[str], float]:
        """
        Use LLM to generate action items and urgency score for a JIRA issue.

        Args:
            issue_data: Dictionary containing JIRA issue information

        Returns:
            Tuple of (action_items_list, urgency_score)
        """
        try:
            # Create system prompt for JIRA analysis
            system_prompt = """You are an expert JIRA issue analyzer. Generate concise, actionable items and urgency scores.

URGENCY SCORING (0.0-1.0):
- P0/Critical bugs with customer impact: 0.8-1.0
- P1/High priority active issues: 0.6-0.8
- P2/Medium priority or routine tasks: 0.4-0.6
- P3/Low priority or completed items: 0.2-0.4
- Closed/resolved issues: 0.1-0.3

ACTION ITEMS RULES:
- Generate ONLY 2-4 essential action items maximum
- Focus on immediate next steps, not generic tasks
- Skip obvious actions like "review requirements" or "coordinate with team"
- Only include items that require specific action or decision
- Keep each item under 15 words
- If issue is resolved/closed, generate 0-1 items maximum
- For issues with no clear actions needed, return empty array

AVOID generating action items for:
- Issues that are already resolved/closed
- Generic project management tasks
- Obvious development steps (testing, code review, documentation)
- Items that don't require immediate attention

Respond with ONLY a JSON object:
{
    "action_items": ["specific action 1", "specific action 2"],
    "score": 0.65
}"""

            # Create user prompt with issue data
            user_prompt = f"""Please analyze this JIRA issue and generate action items and urgency score:

Issue Key: {issue_data.get('key', 'N/A')}
Summary: {issue_data.get('summary', 'N/A')}
Status: {issue_data.get('status', 'N/A')}
Priority: {issue_data.get('priority', 'N/A')}
Issue Type: {issue_data.get('issue_type', 'N/A')}
Assignee: {issue_data.get('assignee', 'N/A')}
Created: {issue_data.get('created', 'N/A')}
Updated: {issue_data.get('updated', 'N/A')}
Due Date: {issue_data.get('due_date', 'N/A')}

Description: {issue_data.get('description', 'N/A')[:1000]}...

Recent Comments: {issue_data.get('recent_comments', 'N/A')[:500]}..."""

            # Call OpenAI API
            response = self.openai_client.chat.completions.create(
                model="gpt-4.1",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                max_tokens=200  # Reduced to encourage concise responses
            )

            # Parse response
            response_text = response.choices[0].message.content.strip()
            result = json.loads(response_text)

            action_items = result.get('action_items', [])
            score = float(result.get('score', 0.5))

            # Ensure score is within bounds
            score = max(0.0, min(1.0, score))

            return action_items, score

        except Exception as e:
            print(f"Warning: LLM analysis failed for issue {issue_data.get('key', 'unknown')}: {e}")
            # Fallback to basic scoring
            fallback_score = self._calculate_fallback_score(issue_data)
            fallback_actions = [f"Review and address {issue_data.get('issue_type', 'issue')}: {issue_data.get('summary', 'No summary')[:100]}"]
            return fallback_actions, fallback_score

    def _calculate_fallback_score(self, issue_data: Dict[str, Any]) -> float:
        """Calculate a basic urgency score without LLM."""
        score = 0.5  # Default medium urgency

        # Adjust based on priority
        priority = issue_data.get('priority', '').lower()
        if 'p0' in priority or 'highest' in priority:
            score = 0.9
        elif 'p1' in priority or 'high' in priority:
            score = 0.7
        elif 'p2' in priority or 'medium' in priority:
            score = 0.5
        elif 'p3' in priority or 'low' in priority:
            score = 0.3
        elif 'p4' in priority or 'lowest' in priority:
            score = 0.1

        # Adjust based on status
        status = issue_data.get('status', '').lower()
        if 'open' in status or 'in progress' in status:
            score += 0.1
        elif 'resolved' in status or 'closed' in status:
            score -= 0.2

        # Adjust based on issue type
        issue_type = issue_data.get('issue_type', '').lower()
        if 'bug' in issue_type:
            score += 0.1

        return max(0.0, min(1.0, score))

    def convert_jira_to_json(self, jira_keys: List[str]) -> List[Dict[str, Any]]:
        """
        Convert JIRA issues to the specified JSON format.

        Args:
            jira_keys: List of JIRA issue keys to process

        Returns:
            List of dictionaries in the specified JSON format
        """
        results = []

        for key in jira_keys:
            try:
                print(f"Processing JIRA issue: {key}")

                # Get issue data
                issue = jira.issue(key)

                # Extract basic information
                summary = issue.fields.summary if issue.fields.summary else "No Summary"
                description = issue.fields.description if issue.fields.description else "No description provided."

                # Get recent comments for context
                recent_comments = ""
                if issue.fields.comment.comments:
                    recent_comments = "\n".join([
                        f"{comment.author.displayName}: {comment.body}"
                        for comment in issue.fields.comment.comments[-3:]  # Last 3 comments
                    ])

                # Prepare issue data for LLM analysis
                issue_data = {
                    'key': key,
                    'summary': summary,
                    'description': description,
                    'status': getattr(issue.fields.status, 'name', 'Unknown') if issue.fields.status else 'Unknown',
                    'priority': getattr(issue.fields.priority, 'name', 'Unknown') if issue.fields.priority else 'Unknown',
                    'issue_type': getattr(issue.fields.issuetype, 'name', 'Unknown') if issue.fields.issuetype else 'Unknown',
                    'assignee': getattr(issue.fields.assignee, 'displayName', 'Unassigned') if issue.fields.assignee else 'Unassigned',
                    'created': issue.fields.created if issue.fields.created else 'Unknown',
                    'updated': issue.fields.updated if issue.fields.updated else 'Unknown',
                    'due_date': issue.fields.duedate if issue.fields.duedate else 'No due date',
                    'recent_comments': recent_comments
                }

                # Generate action items and score using LLM
                action_items, urgency_score = self._generate_action_items_and_score(issue_data)

                # Generate short summary using LLM
                short_summary = self._generate_short_summary(issue_data)

                # Create the JSON entry
                json_entry = {
                    "source": "jira",
                    "link": f"{JIRA_SERVER}/browse/{key}",
                    "timestamp": self._parse_jira_timestamp(issue.fields.updated),
                    "title": f"{key}: {summary}"[:200],  # Limit to 200 characters
                    "long_summary": short_summary,
                    "action_items": action_items,
                    "score": round(urgency_score, 2)
                }

                results.append(json_entry)

            except Exception as e:
                print(f"Error processing JIRA issue {key}: {e}")
                continue

        return results


def generate_jira_json_output() -> List[Dict[str, Any]]:
    """
    Main function to generate JSON output for JIRA issues.

    Returns:
        List of dictionaries in the specified JSON format
    """
    # Find JIRA keys using existing function
    keys = find_jira_keys_by_conditions()

    if not keys:
        print("No JIRA issues found matching the conditions.")
        return []

    # Initialize processor and convert to JSON
    processor = JiraJSONProcessor()
    return processor.convert_jira_to_json(keys)


# if __name__ == "__main__":
#     # You can choose which function to run:
#     # main()  # Original markdown generation

#     # Or generate JSON output:
#     json_results = generate_jira_json_output()
#     print(json.dumps(json_results, indent=2))
