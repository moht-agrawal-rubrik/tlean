# GitHub Candidate Generator - Planning Document

## Overview
This document outlines the implementation plan for enhancing the GitHub candidate generator to process PR data according to the guidelines.md schema and generate actionable insights.

## Current State Analysis

### Existing Components
1. **GitHubCandidateGenerator** (`github_candidate_generator.py`)
   - Fetches PR data from GitHub API
   - Basic data structuring
   - Placeholder LLM processing
   - Simple urgency scoring

2. **Data Structure** (`result.json`)
   - Contains sample PR data with comprehensive metadata
   - Includes global and inline comments
   - Has reviewer and assignee information

### Required Output Format (from guidelines.md)
```json
[
  {
     "source": "github" | "jira" | "slack",
     "link": "<link of the original source>",
     "timestamp": "<in utc>",  (eg. 2025-09-10 04:25:21)
     "title": "string", (max 200 characters)
     "long_summary": "string", (less than 1000 characters ~ 200 words)
     "action_items": [ 
        "item 1",
        "item 2",
         ...
     ],
     "score": 0.69 (floating point describing urgency)
  }
]
```

## Implementation Plan

### Task 1: Data Processing Function
**Objective**: Create a function that transforms raw GitHub PR data into the required format

**Function Signature**:
```python
def process_github_pr_data(raw_pr_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process raw GitHub PR data into the required candidate format.
    
    Args:
        raw_pr_data: Raw PR data from GitHub API (as in result.json)
        
    Returns:
        Processed data in guidelines.md format
    """
```

**Key Processing Steps**:
1. Extract basic metadata (source, link, timestamp)
2. Generate concise title (max 200 chars)
3. Create long_summary (max 1000 chars)
4. Generate action_items list
5. Calculate urgency score

### Task 2: Scoring Algorithm Design
**Objective**: Create a deterministic/probabilistic heuristic for PR urgency scoring

**Scoring Parameters**:
1. **Time Factor** (0.0 - 0.4 weight)
   - PR creation time vs current time
   - Last update time vs current time
   - Time since last reviewer activity

2. **Reviewer Factor** (0.0 - 0.3 weight)
   - Number of assigned reviewers
   - Number of reviewers who have commented
   - Reviewer response time patterns

3. **Comment Factor** (0.0 - 0.3 weight)
   - Total number of comments requiring response
   - Number of unresolved inline comments
   - Comment sentiment/urgency indicators

**Mathematical Approach**:
- Base score: 0.1
- Time decay function for aging PRs
- Reviewer engagement multiplier
- Comment urgency boost
- Final normalization to 0.0-1.0 range

### Task 3: Action Items Generation
**Objective**: Extract actionable items from PR comments and metadata

**Action Item Sources**:
1. **Pending Comments**
   - Inline comments without author responses
   - Review comments marked as "changes requested"
   - Discussion threads without resolution

2. **PR Status Actions**
   - Approval requirements
   - CI/CD failures
   - Merge conflicts

3. **Bot Comment Filtering**
   - Filter out comments from `rubrik-alfred[bot]`
   - Filter out other automated bot accounts
   - Focus on human reviewer comments

**Action Item Categories**:
- Code review responses needed
- Technical changes required
- Documentation updates
- Testing requirements
- Approval workflows

### Task 4: Integration Strategy
**Objective**: Integrate all components into a cohesive processing pipeline

**Integration Points**:
1. Enhance existing `GitHubCandidateGenerator.process_with_llm()`
2. Replace placeholder scoring with new algorithm
3. Implement comprehensive action item extraction
4. Ensure output format compliance

**Testing Strategy**:
1. Use existing `result.json` as test data
2. Validate output format against guidelines.md schema
3. Test edge cases (no comments, bot-only comments, etc.)
4. Performance testing with multiple PRs

## Implementation Details

### Data Flow
```
Raw GitHub PR Data (result.json format)
    ↓
Data Processing Function
    ↓ (parallel processing)
    ├── Title Generation
    ├── Summary Creation  
    ├── Action Items Extraction
    └── Score Calculation
    ↓
Guidelines.md Format Output
```

### Error Handling
- Graceful handling of missing data fields
- Default values for optional parameters
- Logging for debugging and monitoring

### Performance Considerations
- Efficient comment parsing
- Minimal API calls for additional data
- Caching for repeated processing

## Next Steps
1. Create detailed scoring algorithm documentation
2. Implement data processing function
3. Build action items extraction logic
4. Integration and testing
5. Documentation and examples

## Success Criteria
- Output matches guidelines.md schema exactly
- Scoring algorithm produces meaningful urgency rankings
- Action items are relevant and actionable
- Bot comments are properly filtered
- Function handles edge cases gracefully
