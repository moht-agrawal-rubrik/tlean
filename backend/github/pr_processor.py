"""
Enhanced PR data processor that converts GitHub PR data to guidelines.md format.
"""

import re
import math
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional


class PRProcessor:
    """Processes GitHub PR data into the required candidate format."""
    
    # Bot patterns to filter out automated comments
    BOT_PATTERNS = [
        'rubrik-alfred[bot]',
        'rogers-sail-information[bot]',
        'polaris-jenkins-sails[bot]',
        'rubrik-stark-edith[bot]',
        'SD-111029',  # Automated system account
        '[bot]'  # Generic bot pattern
    ]
    
    def __init__(self):
        """Initialize the processor."""
        pass
    
    def process_pr_data(self, raw_pr_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process raw GitHub PR data into the required candidate format.
        
        Args:
            raw_pr_data: Raw PR data from GitHub API (as in result.json format)
            
        Returns:
            Processed data in guidelines.md format
        """
        # Extract basic information
        source = "github"
        link = raw_pr_data.get('pr_url', '')
        timestamp = self._format_timestamp(raw_pr_data.get('metadata', {}).get('created_at'))
        
        # Generate title (max 200 characters)
        title = self._generate_title(raw_pr_data)
        
        # Create long summary (max 1000 characters)
        long_summary = self._generate_summary(raw_pr_data)
        
        # Generate action items
        action_items = self._generate_action_items(raw_pr_data)
        
        # Calculate urgency score
        score = self._calculate_urgency_score(raw_pr_data)
        
        return {
            "source": source,
            "link": link,
            "timestamp": timestamp,
            "title": title,
            "long_summary": long_summary,
            "action_items": action_items,
            "score": score
        }
    
    def _format_timestamp(self, iso_timestamp: Optional[str]) -> str:
        """Convert ISO timestamp to required format."""
        if not iso_timestamp:
            return datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
        
        try:
            # Parse ISO timestamp and convert to UTC
            dt = datetime.fromisoformat(iso_timestamp.replace('Z', '+00:00'))
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except (ValueError, AttributeError):
            return datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
    
    def _generate_title(self, pr_data: Dict[str, Any]) -> str:
        """Generate a concise title (max 200 characters)."""
        pr_title = pr_data.get('pr_title', 'GitHub PR')
        pr_number = pr_data.get('metadata', {}).get('number', '')
        
        # Create a descriptive title
        if pr_number:
            title = f"PR #{pr_number}: {pr_title}"
        else:
            title = f"GitHub PR: {pr_title}"
        
        # Truncate if too long
        if len(title) > 200:
            title = title[:197] + "..."
        
        return title
    
    def _generate_summary(self, pr_data: Dict[str, Any]) -> str:
        """Generate a comprehensive summary (max 1000 characters)."""
        pr_summary = pr_data.get('pr_summary', '')
        metadata = pr_data.get('metadata', {})
        
        # Extract key information
        author = metadata.get('author', 'Unknown')
        state = metadata.get('state', 'unknown')
        reviewers = metadata.get('reviewers', [])
        assignees = metadata.get('assignees', [])
        
        # Build summary
        summary_parts = []
        
        # Add PR description (truncated)
        if pr_summary:
            # Clean up the summary (remove markdown artifacts)
            clean_summary = re.sub(r'#{1,6}\s+', '', pr_summary)  # Remove headers
            clean_summary = re.sub(r'\r\n|\r|\n', ' ', clean_summary)  # Replace newlines
            clean_summary = re.sub(r'\s+', ' ', clean_summary).strip()  # Normalize whitespace
            
            if len(clean_summary) > 400:
                clean_summary = clean_summary[:397] + "..."
            summary_parts.append(clean_summary)
        
        # Add metadata information
        meta_info = f"Author: {author}, State: {state}"
        if reviewers:
            meta_info += f", Reviewers: {len(reviewers)}"
        if assignees:
            meta_info += f", Assignees: {len(assignees)}"
        
        summary_parts.append(meta_info)
        
        # Combine and ensure length limit
        full_summary = ". ".join(summary_parts)
        if len(full_summary) > 1000:
            full_summary = full_summary[:997] + "..."
        
        return full_summary
    
    def _generate_action_items(self, pr_data: Dict[str, Any]) -> List[str]:
        """Generate action items from PR data."""
        action_items = []
        
        # Get comments and metadata
        comments = pr_data.get('comments', {})
        global_comments = comments.get('global_comments', [])
        inline_comments = comments.get('inline_comments', [])
        metadata = pr_data.get('metadata', {})
        author = metadata.get('author', '')
        
        # Filter out bot comments
        human_global_comments = [c for c in global_comments if not self._is_bot_comment(c)]
        human_inline_comments = [c for c in inline_comments if not self._is_bot_comment(c)]
        
        # Find pending responses in global comments
        pending_global = self._find_pending_responses(human_global_comments, author)
        if pending_global > 0:
            action_items.append(f"Respond to {pending_global} pending discussion comment(s)")
        
        # Find pending responses in inline comments
        pending_inline = self._find_pending_responses(human_inline_comments, author)
        if pending_inline > 0:
            action_items.append(f"Address {pending_inline} pending code review comment(s)")
        
        # Check PR state for additional actions
        state = metadata.get('state', '')
        if state == 'open':
            reviewers = metadata.get('reviewers', [])
            if reviewers:
                action_items.append("Await reviewer approval")
            else:
                action_items.append("Request code review")
        
        # Check for merge conflicts or CI failures (if indicated in comments)
        for comment in human_global_comments:
            body = comment.get('body', '').lower()
            if 'conflict' in body or 'merge conflict' in body:
                action_items.append("Resolve merge conflicts")
                break
        
        # If no specific actions found, add a general review action
        if not action_items and state == 'open':
            action_items.append("Review and merge PR")
        
        return action_items
    
    def _is_bot_comment(self, comment: Dict[str, Any]) -> bool:
        """Check if a comment is from a bot account."""
        author = comment.get('author', '')
        return any(pattern in author for pattern in self.BOT_PATTERNS)
    
    def _find_pending_responses(self, comments: List[Dict[str, Any]], author: str) -> int:
        """Find comments that need responses from the PR author."""
        pending_count = 0
        
        # Sort comments by creation time
        sorted_comments = sorted(comments, key=lambda x: x.get('created_at', ''))
        
        # Track which non-author comments need responses
        for i, comment in enumerate(sorted_comments):
            comment_author = comment.get('author', '')
            
            # Skip author's own comments
            if comment_author == author:
                continue
            
            # Check if author responded after this comment
            has_response = False
            for j in range(i + 1, len(sorted_comments)):
                later_comment = sorted_comments[j]
                if later_comment.get('author') == author:
                    has_response = True
                    break
            
            if not has_response:
                pending_count += 1
        
        return pending_count
    
    def _calculate_urgency_score(self, pr_data: Dict[str, Any]) -> float:
        """Calculate urgency score based on the algorithm in scoring_algorithm.md."""
        base_score = 0.1
        
        # Extract data
        metadata = pr_data.get('metadata', {})
        comments = pr_data.get('comments', {})
        
        # Time factor (0.4 weight)
        time_factor = self._calculate_time_factor(metadata)
        
        # Reviewer factor (0.3 weight)
        reviewer_factor = self._calculate_reviewer_factor(metadata, comments)
        
        # Comment factor (0.3 weight)
        comment_factor = self._calculate_comment_factor(comments, metadata.get('author', ''))
        
        # Calculate raw score
        raw_score = base_score + time_factor + reviewer_factor + comment_factor
        
        # Apply modifiers
        final_score = self._apply_score_modifiers(raw_score, metadata)
        
        return min(1.0, max(0.0, final_score))
    
    def _calculate_time_factor(self, metadata: Dict[str, Any]) -> float:
        """Calculate time-based urgency factor."""
        try:
            created_at = metadata.get('created_at', '')
            updated_at = metadata.get('updated_at', '')
            
            if not created_at or not updated_at:
                return 0.2  # Default moderate urgency
            
            now = datetime.now(timezone.utc)
            created = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            updated = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
            
            age_days = (now - created).days
            staleness_days = (now - updated).days
            
            # Age scoring (exponential decay)
            age_score = min(1.0, 1.0 - math.exp(-age_days / 7.0))
            
            # Staleness scoring (linear with cap)
            staleness_score = min(1.0, staleness_days / 14.0)
            
            return 0.2 * age_score + 0.2 * staleness_score
            
        except (ValueError, TypeError):
            return 0.2  # Default on error
    
    def _calculate_reviewer_factor(self, metadata: Dict[str, Any], comments: Dict[str, Any]) -> float:
        """Calculate reviewer-based urgency factor."""
        reviewers = metadata.get('reviewers', [])
        assignees = metadata.get('assignees', [])
        total_reviewers = max(len(reviewers), len(assignees), 1)
        
        # Reviewer load scoring (inverse relationship)
        reviewer_load_score = min(1.0, 1.0 / math.sqrt(total_reviewers))
        
        # Review engagement scoring
        all_comments = comments.get('global_comments', []) + comments.get('inline_comments', [])
        human_comments = [c for c in all_comments if not self._is_bot_comment(c)]
        
        reviewers_who_commented = set()
        for comment in human_comments:
            author = comment.get('author', '')
            if author in reviewers or author in assignees:
                reviewers_who_commented.add(author)
        
        engagement_rate = len(reviewers_who_commented) / total_reviewers if total_reviewers > 0 else 0
        engagement_score = 1.0 - engagement_rate
        
        return 0.15 * reviewer_load_score + 0.15 * engagement_score
    
    def _calculate_comment_factor(self, comments: Dict[str, Any], author: str) -> float:
        """Calculate comment-based urgency factor."""
        all_comments = comments.get('global_comments', []) + comments.get('inline_comments', [])
        human_comments = [c for c in all_comments if not self._is_bot_comment(c)]
        
        # Pending responses calculation
        pending_responses = self._find_pending_responses(human_comments, author)
        
        # Pending response scoring (logarithmic growth)
        pending_score = min(1.0, math.log(pending_responses + 1) / math.log(10)) if pending_responses > 0 else 0
        
        # Comment density scoring
        total_human_comments = len(human_comments)
        density_score = min(1.0, total_human_comments / 20.0)
        
        return 0.2 * pending_score + 0.1 * density_score
    
    def _apply_score_modifiers(self, raw_score: float, metadata: Dict[str, Any]) -> float:
        """Apply final modifiers to the score."""
        state = metadata.get('state', '')
        labels = metadata.get('labels', [])
        
        # State modifiers
        if state == 'draft':
            raw_score *= 0.5
        elif state == 'open':
            raw_score *= 1.0  # No change for open PRs
        
        # Label modifiers
        label_names = [label.lower() if isinstance(label, str) else str(label).lower() for label in labels]
        if any('urgent' in label for label in label_names):
            raw_score = min(1.0, raw_score * 1.3)
        elif any('low' in label and 'priority' in label for label in label_names):
            raw_score *= 0.7
        
        return raw_score


def process_github_pr_data(raw_pr_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convenience function to process a single PR data object.
    
    Args:
        raw_pr_data: Raw PR data from GitHub API
        
    Returns:
        Processed data in guidelines.md format
    """
    processor = PRProcessor()
    return processor.process_pr_data(raw_pr_data)
