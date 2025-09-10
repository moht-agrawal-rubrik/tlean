"""
JIRA module for processing JIRA issues and generating JSON output.
"""

# Import main classes and functions for easy access
import importlib.util
import os

# Load the jira-main module dynamically since it has a hyphen in the name
spec = importlib.util.spec_from_file_location("jira_main", os.path.join(os.path.dirname(__file__), "jira-main.py"))
jira_main = importlib.util.module_from_spec(spec)
spec.loader.exec_module(jira_main)

# Import the classes and functions
JiraJSONProcessor = jira_main.JiraJSONProcessor
generate_jira_json_output = jira_main.generate_jira_json_output
find_jira_keys_by_conditions = jira_main.find_jira_keys_by_conditions
get_full_markdown = jira_main.get_full_markdown

__all__ = [
    'JiraJSONProcessor',
    'generate_jira_json_output', 
    'find_jira_keys_by_conditions',
    'get_full_markdown'
]
