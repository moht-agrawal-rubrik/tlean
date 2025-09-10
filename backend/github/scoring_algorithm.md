# PR Urgency Scoring Algorithm

## Overview
This document defines a mathematical approach for calculating urgency scores for GitHub Pull Requests. The score ranges from 0.0 to 1.0, where higher values indicate more urgent PRs requiring immediate attention.

## Scoring Components

### 1. Time Factor (Weight: 0.4)
Time-based urgency considers how long the PR has been waiting for action.

#### Sub-components:
- **Age Factor (0.2)**: How long since PR creation
- **Staleness Factor (0.2)**: How long since last meaningful update

#### Mathematical Formula:

```
age_days = (current_time - pr_created_at).days
staleness_days = (current_time - pr_updated_at).days

# Age scoring (exponential decay)
age_score = min(1.0, 1.0 - exp(-age_days / 7.0))

# Staleness scoring (linear decay with cap)
staleness_score = min(1.0, staleness_days / 14.0)

time_factor = 0.2 * age_score + 0.2 * staleness_score
```

#### Rationale:
- PRs become more urgent as they age (prevents stale PRs)
- Recent updates reduce urgency (active development)
- Exponential decay for age prevents infinite growth
- 7-day half-life for age factor (weekly sprint cycles)
- 14-day cap for staleness (maximum staleness urgency)

### 2. Reviewer Factor (Weight: 0.3)
Measures reviewer engagement and bottlenecks.

#### Sub-components:
- **Reviewer Load (0.15)**: Number of assigned reviewers
- **Review Engagement (0.15)**: Reviewer participation rate

#### Mathematical Formula:

```
num_reviewers = len(pr_metadata['reviewers'])
num_assignees = len(pr_metadata['assignees'])
total_reviewers = max(num_reviewers, num_assignees, 1)

# Reviewer load scoring (inverse relationship)
reviewer_load_score = min(1.0, 1.0 / sqrt(total_reviewers))

# Review engagement scoring
reviewers_who_commented = count_unique_reviewer_comments(comments)
engagement_rate = reviewers_who_commented / total_reviewers if total_reviewers > 0 else 0
engagement_score = 1.0 - engagement_rate

reviewer_factor = 0.15 * reviewer_load_score + 0.15 * engagement_score
```

#### Rationale:
- Fewer reviewers = higher urgency (bottleneck risk)
- Low reviewer engagement = higher urgency (needs attention)
- Square root scaling prevents extreme penalties for many reviewers

### 3. Comment Factor (Weight: 0.3)
Analyzes comment patterns to identify PRs needing responses.

#### Sub-components:
- **Pending Responses (0.2)**: Comments requiring author action
- **Comment Density (0.1)**: Overall discussion volume

#### Mathematical Formula:

```
# Filter out bot comments
human_comments = filter_bot_comments(all_comments)
author_username = pr_metadata['author']

# Pending responses calculation
pending_responses = 0
for comment in human_comments:
    if comment['author'] != author_username:
        # Check if author responded after this comment
        if not has_author_response_after(comment, human_comments, author_username):
            pending_responses += 1

# Pending response scoring (logarithmic growth)
pending_score = min(1.0, log(pending_responses + 1) / log(10))

# Comment density scoring
total_human_comments = len(human_comments)
density_score = min(1.0, total_human_comments / 20.0)

comment_factor = 0.2 * pending_score + 0.1 * density_score
```

#### Rationale:
- Unanswered reviewer comments indicate urgent action needed
- Logarithmic scaling prevents extreme scores for very active PRs
- High comment density suggests complex/important PR
- Bot comments filtered to focus on human interaction

## Final Score Calculation

### Base Score and Normalization:

```
base_score = 0.1  # Minimum urgency for any open PR

raw_score = base_score + time_factor + reviewer_factor + comment_factor
final_score = min(1.0, raw_score)
```

### Special Modifiers:

#### PR State Modifiers:
```
if pr_state == 'draft':
    final_score *= 0.5  # Draft PRs less urgent
elif pr_state == 'ready_for_review':
    final_score *= 1.2  # Ready PRs more urgent
```

#### Label-based Modifiers:
```
labels = pr_metadata.get('labels', [])
if 'urgent' in [label.lower() for label in labels]:
    final_score = min(1.0, final_score * 1.3)
elif 'low-priority' in [label.lower() for label in labels]:
    final_score *= 0.7
```

## Implementation Considerations

### Bot Comment Filtering:
```python
BOT_PATTERNS = [
    'rubrik-alfred[bot]',
    'rogers-sail-information[bot]',
    'polaris-jenkins-sails[bot]',
    'rubrik-stark-edith[bot]',
    'SD-111029'  # Automated system account
]

def is_bot_comment(comment):
    author = comment.get('author', '')
    return any(pattern in author for pattern in BOT_PATTERNS)
```

### Edge Cases:
1. **No Comments**: Comment factor = 0.1 (base density)
2. **No Reviewers**: Reviewer factor = 0.15 (maximum urgency)
3. **Very Old PRs**: Time factor capped at 0.4
4. **All Bot Comments**: Pending responses = 0

## Example Calculations

### Example 1: Fresh PR with Active Review
```
- Created: 2 days ago
- Updated: 1 day ago  
- Reviewers: 3
- Comments: 5 (2 from reviewers, 1 pending response)

age_score = 1.0 - exp(-2/7) ≈ 0.25
staleness_score = 1/14 ≈ 0.07
time_factor = 0.2 * 0.25 + 0.2 * 0.07 = 0.064

reviewer_load_score = 1/sqrt(3) ≈ 0.58
engagement_score = 1 - (2/3) ≈ 0.33
reviewer_factor = 0.15 * 0.58 + 0.15 * 0.33 = 0.137

pending_score = log(2)/log(10) ≈ 0.30
density_score = 5/20 = 0.25
comment_factor = 0.2 * 0.30 + 0.1 * 0.25 = 0.085

final_score = 0.1 + 0.064 + 0.137 + 0.085 = 0.386
```

### Example 2: Stale PR Needing Attention
```
- Created: 10 days ago
- Updated: 8 days ago
- Reviewers: 1
- Comments: 8 (5 pending responses)

age_score = 1.0 - exp(-10/7) ≈ 0.76
staleness_score = min(1.0, 8/14) ≈ 0.57
time_factor = 0.2 * 0.76 + 0.2 * 0.57 = 0.266

reviewer_load_score = 1/sqrt(1) = 1.0
engagement_score = 1 - (1/1) = 0
reviewer_factor = 0.15 * 1.0 + 0.15 * 0 = 0.15

pending_score = log(6)/log(10) ≈ 0.78
density_score = 8/20 = 0.4
comment_factor = 0.2 * 0.78 + 0.1 * 0.4 = 0.196

final_score = 0.1 + 0.266 + 0.15 + 0.196 = 0.712
```

## Validation and Tuning

### Expected Score Ranges:
- **0.0-0.3**: Low urgency (new PRs, well-managed)
- **0.3-0.6**: Medium urgency (normal review process)
- **0.6-0.8**: High urgency (needs attention)
- **0.8-1.0**: Critical urgency (blocking/stale)

### Tuning Parameters:
- Adjust weights based on team preferences
- Modify decay constants for different sprint cycles
- Customize bot patterns for organization
- Add domain-specific label modifiers
