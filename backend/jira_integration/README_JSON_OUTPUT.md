# JIRA JSON Output Functionality

This document describes the new JSON output functionality for JIRA issues, which provides a structured format suitable for AI-ready action item generation and urgency scoring.

## Overview

The new functionality converts JIRA issues into a standardized JSON format that includes:
- Source identification
- Direct links to original issues
- Timestamps in UTC format
- Concise titles and summaries
- LLM-generated action items
- Urgency scoring (0.0 to 1.0)

## JSON Output Format

Each JIRA issue is converted to the following JSON structure:

```json
{
  "source": "jira",
  "link": "https://your-jira-server.com/browse/ISSUE-123",
  "timestamp": "2025-09-10 04:25:21",
  "title": "ISSUE-123: Brief description of the issue",
  "long_summary": "Detailed description of the issue (max 1000 characters)",
  "action_items": [
    "Review and analyze the reported bug",
    "Assign to appropriate team member",
    "Create test cases to reproduce the issue"
  ],
  "score": 0.75
}
```

## Key Features

### 1. LLM-Powered Action Items
- Uses OpenAI GPT-4.1 to analyze JIRA issues
- Generates specific, actionable tasks
- Considers issue context, description, and comments

### 2. Intelligent Urgency Scoring
- Factors in priority level, status, issue type, and severity
- Considers due dates and recent activity
- Provides fallback scoring when LLM is unavailable

### 3. Timestamp Normalization
- Converts JIRA timestamps to UTC format
- Standardized format: `YYYY-MM-DD HH:MM:SS`

### 4. Content Optimization
- Titles limited to 200 characters
- Summaries limited to 1000 characters
- Handles missing or null fields gracefully

## Usage

### Basic Usage

```python
from jira-main import generate_jira_json_output

# Get open assigned JIRA issues as JSON (limited to 10)
json_results = generate_jira_json_output()
print(json.dumps(json_results, indent=2))
```

### Processing Specific Issues

```python
from jira-main import JiraJSONProcessor

# Process specific JIRA keys
processor = JiraJSONProcessor()
specific_keys = ["CDM-12345", "CDM-67890"]
results = processor.convert_jira_to_json(specific_keys)
```

### Filtering by Urgency

```python
# Filter high-urgency issues
high_urgency = [item for item in json_results if item['score'] >= 0.7]
```

## Configuration

### Environment Variables

Ensure these environment variables are set in your `.env` file:

```bash
# JIRA Configuration
JIRA_SERVER=https://your-jira-server.com
USERNAME=your-jira-username
API_TOKEN=your-jira-api-token

# OpenAI Configuration (for LLM analysis)
OPENAI_API_KEY=your-openai-api-key
```

### Dependencies

The functionality requires these Python packages:
- `jira` - JIRA API client
- `openai` - OpenAI API client
- `requests` - HTTP requests
- `python-dotenv` - Environment variable loading

## Urgency Scoring Algorithm

The urgency score (0.0 to 1.0) is calculated based on:

### Primary Factors
- **Priority Level**: P0=1.0, P1=0.8, P2=0.6, P3=0.4, P4=0.2
- **Status**: Open/In Progress = higher, Resolved/Closed = lower
- **Issue Type**: Bug = higher, Task/Story = medium

### Secondary Factors
- Severity level
- Due date proximity
- Recent activity/updates
- Customer impact indicators

### Fallback Scoring
When LLM analysis fails, a rule-based fallback system provides basic scoring based on priority, status, and issue type.

## Error Handling

The system includes comprehensive error handling:
- Graceful degradation when LLM is unavailable
- Fallback scoring for failed analyses
- Timestamp parsing with fallbacks
- Skips problematic issues and continues processing

## Testing

### Run Tests
```bash
cd backend/jira
python test_json_output.py
```

### Example Usage
```bash
python example_json_usage.py
```

## Integration with Other Sources

This JSON format is designed to be compatible with similar outputs from:
- GitHub PR processing
- Slack conversation analysis
- Other issue tracking systems

All sources use the same JSON schema for consistent processing and analysis.

## Performance Considerations

- LLM calls are made sequentially to avoid rate limiting
- Large descriptions are truncated to manage token usage
- Recent comments (last 3) are included for context
- Processing time scales with number of issues and LLM response time

## Troubleshooting

### Common Issues

1. **LLM Analysis Fails**: Check OpenAI API key and network connectivity
2. **JIRA Connection Issues**: Verify JIRA credentials and server URL
3. **Timestamp Parsing Errors**: Check JIRA timestamp format compatibility
4. **Missing Action Items**: Verify issue has sufficient content for analysis

### Debug Mode

Enable debug output by modifying the processor initialization:
```python
processor = JiraJSONProcessor()
# Add debug prints in the _generate_action_items_and_score method
```

## Future Enhancements

Potential improvements:
- Batch LLM processing for better performance
- Custom scoring models for different issue types
- Integration with JIRA webhooks for real-time updates
- Support for additional JIRA custom fields
- Caching of LLM responses to reduce API calls
