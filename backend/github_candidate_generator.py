#!/usr/bin/env python3
"""
GitHub Candidate Generator
Part of the modular candidate generation system for fetching GitHub PR data
and generating action items using LLMs.
"""

import os
import re
import json
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class GitHubCandidateGenerator:
    """
    GitHub candidate generator for the modular todo/kanban system.
    
    Responsibilities:
    1. Fetch PR data from GitHub
    2. Process data with LLM to generate titles, summaries, and action items
    3. Return standardized candidate format for ranking system
    """
    
    def __init__(self, github_token: Optional[str] = None):
        """
        Initialize the GitHub candidate generator.
        
        Args:
            github_token: GitHub personal access token (optional)
        """
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'GitHub-Candidate-Generator/1.0'
        })
        
        if github_token:
            self.session.headers['Authorization'] = f'token {github_token}'
        else:
            raise ValueError("GitHub token is required")
        
        self.base_url = 'https://api.github.com'
    
    def parse_pr_url(self, url: str) -> tuple:
        """
        Parse GitHub PR URL to extract owner, repo, and PR number.
        
        Args:
            url: GitHub PR URL
            
        Returns:
            Tuple of (owner, repo, pr_number)
        """
        patterns = [
            r'github\.com/([^/]+)/([^/]+)/pull/(\d+)',
            r'api\.github\.com/repos/([^/]+)/([^/]+)/pulls/(\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1), match.group(2), int(match.group(3))
        
        raise ValueError(f"Invalid GitHub PR URL: {url}")
    
    def fetch_pr_data(self, owner: str, repo: str, pr_number: int) -> Dict[str, Any]:
        """
        Fetch comprehensive PR data from GitHub API.
        
        Args:
            owner: Repository owner
            repo: Repository name
            pr_number: Pull request number
            
        Returns:
            Dictionary containing all PR data in standardized format
        """
        try:
            # Fetch main PR data
            pr_url = f"{self.base_url}/repos/{owner}/{repo}/pulls/{pr_number}"
            response = self.session.get(pr_url)
            response.raise_for_status()
            pr_data = response.json()
            
            # Fetch comments
            issue_comments, review_comments = self._fetch_comments(owner, repo, pr_number)
            
            # Fetch reviews
            reviews = self._fetch_reviews(owner, repo, pr_number)
            
            # Fetch files (limited for performance)
            files = self._fetch_files(owner, repo, pr_number, limit=20)
            
            # Structure data according to our JSON schema
            structured_data = self._structure_pr_data(
                pr_data, issue_comments, review_comments, reviews, files
            )
            
            return structured_data
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                raise ValueError(f"PR not found: {owner}/{repo}/pull/{pr_number}")
            elif e.response.status_code == 403:
                raise ValueError("Rate limit exceeded. Please provide a GitHub token.")
            else:
                raise
        except Exception as e:
            raise Exception(f"Failed to fetch PR data: {str(e)}")
    
    def _fetch_comments(self, owner: str, repo: str, pr_number: int) -> tuple:
        """Fetch both issue comments and review comments."""
        # Issue comments (global discussion)
        issue_url = f"{self.base_url}/repos/{owner}/{repo}/issues/{pr_number}/comments"
        issue_response = self.session.get(issue_url)
        issue_response.raise_for_status()
        issue_comments = issue_response.json()
        
        # Review comments (inline code comments)
        review_url = f"{self.base_url}/repos/{owner}/{repo}/pulls/{pr_number}/comments"
        review_response = self.session.get(review_url)
        review_response.raise_for_status()
        review_comments = review_response.json()
        
        return issue_comments, review_comments
    
    def _fetch_reviews(self, owner: str, repo: str, pr_number: int) -> List[Dict]:
        """Fetch PR reviews."""
        reviews_url = f"{self.base_url}/repos/{owner}/{repo}/pulls/{pr_number}/reviews"
        response = self.session.get(reviews_url)
        response.raise_for_status()
        return response.json()
    
    def _fetch_files(self, owner: str, repo: str, pr_number: int, limit: int = 20) -> List[Dict]:
        """Fetch changed files (limited for performance)."""
        files_url = f"{self.base_url}/repos/{owner}/{repo}/pulls/{pr_number}/files"
        response = self.session.get(files_url, params={'per_page': limit})
        response.raise_for_status()
        return response.json()
    
    def _structure_pr_data(self, pr_data: Dict, issue_comments: List[Dict], 
                          review_comments: List[Dict], reviews: List[Dict], 
                          files: List[Dict]) -> Dict[str, Any]:
        """
        Structure PR data according to our standardized JSON schema.
        """
        # Categorize comments
        global_comments = []
        inline_comments = []
        
        # Process issue comments (global)
        for comment in issue_comments:
            global_comments.append({
                "type": "discussion",
                "author": comment['user']['login'] if comment['user'] else "Unknown",
                "created_at": comment['created_at'],
                "body": comment['body'],
                "comment_url": comment['html_url']
            })
        
        # Process review summary comments (global)
        for review in reviews:
            if review.get('body'):  # Only reviews with summary comments
                global_comments.append({
                    "type": "review_summary",
                    "author": review['user']['login'] if review['user'] else "Unknown",
                    "created_at": review['submitted_at'],
                    "body": review['body'],
                    "comment_url": review['html_url']
                })
        
        # Process review comments (inline)
        for comment in review_comments:
            inline_comments.append({
                "author": comment['user']['login'] if comment['user'] else "Unknown",
                "created_at": comment['created_at'],
                "body": comment['body'],
                "file_path": comment.get('path', 'Unknown'),
                "line_number": comment.get('line') or comment.get('original_line'),
                "diff_hunk": comment.get('diff_hunk'),
                "comment_url": comment['html_url']
            })
        
        # Structure files data
        files_changed = []
        for file in files:
            files_changed.append({
                "filename": file['filename'],
                "status": file['status'],
                "additions": file['additions'],
                "deletions": file['deletions'],
                "patch": file.get('patch')  # May be None for large files
            })
        
        # Build final structure
        return {
            "pr_title": pr_data['title'],
            "pr_summary": pr_data.get('body', ''),
            "pr_url": pr_data['html_url'],
            "metadata": {
                "number": pr_data['number'],
                "state": pr_data['state'],
                "author": pr_data['user']['login'] if pr_data['user'] else "Unknown",
                "created_at": pr_data['created_at'],
                "updated_at": pr_data['updated_at'],
                "merged_at": pr_data.get('merged_at'),
                "base_branch": pr_data['base']['ref'],
                "head_branch": pr_data['head']['ref'],
                "labels": [label['name'] for label in pr_data.get('labels', [])],
                "assignees": [user['login'] for user in pr_data.get('assignees', [])],
                "reviewers": [user['login'] for user in pr_data.get('requested_reviewers', [])]
            },
            "comments": {
                "global_comments": global_comments,
                "inline_comments": inline_comments
            },
            "files_changed": files_changed,
            "statistics": {
                "commits": pr_data.get('commits', 0),
                "files_changed": pr_data.get('changed_files', 0),
                "additions": pr_data.get('additions', 0),
                "deletions": pr_data.get('deletions', 0),
                "total_comments": len(global_comments) + len(inline_comments)
            }
        }
    
    def process_with_llm(self, pr_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process PR data with LLM to generate action items.
        
        Args:
            pr_data: Structured PR data
            
        Returns:
            Processed data with LLM-generated content
            
        Note: This is a placeholder for LLM integration
        """
        # TODO: Implement LLM processing
        # This will analyze the PR data and generate:
        # - Enhanced title
        # - Summary
        # - Action items with priorities
        # - Next steps
        # - Urgency score for ranking
        
        # Placeholder implementation
        action_items = []
        
        # Simple heuristics for demo (replace with LLM)
        if pr_data['metadata']['state'] == 'open':
            action_items.append({
                "item": f"Review PR: {pr_data['pr_title']}",
                "priority": "medium",
                "next_steps": ["Read description", "Review code changes", "Test locally"]
            })
        
        if pr_data['comments']['inline_comments']:
            action_items.append({
                "item": "Address code review comments",
                "priority": "high",
                "next_steps": ["Review inline comments", "Make necessary changes", "Respond to reviewers"]
            })
        
        return {
            "source": "github",
            "candidate_id": f"github_pr_{pr_data['metadata']['number']}",
            "raw_data": pr_data,
            "processed_data": {
                "title": f"PR Review: {pr_data['pr_title']}",
                "summary": pr_data['pr_summary'][:200] + "..." if len(pr_data['pr_summary']) > 200 else pr_data['pr_summary'],
                "action_items": action_items,
                "urgency_score": self._calculate_urgency_score(pr_data),
                "context": f"GitHub PR in {pr_data['metadata']['base_branch']} branch"
            }
        }
    
    def _calculate_urgency_score(self, pr_data: Dict[str, Any]) -> float:
        """Calculate urgency score for ranking (0.0 to 1.0)."""
        score = 0.5  # Base score
        
        # Increase urgency for open PRs
        if pr_data['metadata']['state'] == 'open':
            score += 0.2
        
        # Increase urgency for PRs with many comments
        if pr_data['statistics']['total_comments'] > 5:
            score += 0.2
        
        # Increase urgency for PRs with recent activity
        updated_at = datetime.fromisoformat(pr_data['metadata']['updated_at'].replace('Z', '+00:00'))
        days_since_update = (datetime.now(updated_at.tzinfo) - updated_at).days
        if days_since_update < 1:
            score += 0.3
        elif days_since_update < 3:
            score += 0.1
        
        return min(score, 1.0)
    
    def get_pr_candidate(self, pr_url: str) -> Dict[str, Any]:
        """
        Main interface: Fetch a single PR and process it as a candidate.
        
        Args:
            pr_url: GitHub PR URL
            
        Returns:
            Standardized candidate format for ranking system
        """
        owner, repo, pr_number = self.parse_pr_url(pr_url)
        pr_data = self.fetch_pr_data(owner, repo, pr_number)
        return self.process_with_llm(pr_data)
    
    def get_pr_candidates(self, pr_urls: List[str]) -> List[Dict[str, Any]]:
        """
        Fetch multiple PRs as candidates.
        
        Args:
            pr_urls: List of GitHub PR URLs
            
        Returns:
            List of standardized candidates for ranking system
        """
        candidates = []
        for pr_url in pr_urls:
            try:
                candidate = self.get_pr_candidate(pr_url)
                candidates.append(candidate)
            except Exception as e:
                print(f"Failed to process {pr_url}: {e}")
                continue
        
        return candidates


    def fetch_repo_prs(self, owner: str, repo: str, state: str = 'open', limit: int = 10) -> List[Dict[str, Any]]:
        """
        Fetch recent PRs from a repository.

        Args:
            owner: Repository owner
            repo: Repository name
            state: PR state ('open', 'closed', 'all')
            limit: Maximum number of PRs to fetch

        Returns:
            List of standardized candidates
        """
        try:
            prs_url = f"{self.base_url}/repos/{owner}/{repo}/pulls"
            response = self.session.get(prs_url, params={
                'state': state,
                'per_page': limit,
                'sort': 'updated',
                'direction': 'desc'
            })
            response.raise_for_status()
            prs = response.json()

            candidates = []
            for pr in prs:
                try:
                    # Fetch detailed data for each PR
                    pr_data = self.fetch_pr_data(owner, repo, pr['number'])
                    candidate = self.process_with_llm(pr_data)
                    candidates.append(candidate)
                except Exception as e:
                    print(f"Failed to process PR #{pr['number']}: {e}")
                    continue

            return candidates

        except Exception as e:
            raise Exception(f"Failed to fetch PRs from {owner}/{repo}: {str(e)}")

    def fetch_user_prs(self, username: str, state: str = 'open', limit: int = 20) -> List[Dict[str, Any]]:
        """
        Fetch PRs assigned to or created by a user across all repositories.

        Args:
            username: GitHub username
            state: PR state ('open', 'closed', 'all')
            limit: Maximum number of PRs to fetch

        Returns:
            List of standardized candidates
        """
        try:
            # Search for PRs involving the user
            search_url = f"{self.base_url}/search/issues"
            query = f"type:pr author:{username} state:{state}"

            log_data = {
                "search_url": search_url,
                "params": {
                    'q': query,
                    'per_page': limit,
                    'sort': 'updated',
                    'order': 'desc'
                }
            }

            print(log_data)

            response = self.session.get(search_url, params={
                'q': query,
                'per_page': limit,
                'sort': 'updated',
                'order': 'desc'
            })
            response.raise_for_status()
            search_results = response.json()

            candidates = []
            for item in search_results.get('items', []):
                try:
                    # Extract repo info from URL
                    pr_url = item['html_url']
                    candidate = self.get_pr_candidate(pr_url)
                    candidates.append(candidate)
                except Exception as e:
                    print(f"Failed to process PR {item['html_url']}: {e}")
                    continue

            return candidates

        except Exception as e:
            raise Exception(f"Failed to fetch PRs for user {username}: {str(e)}")


# Convenience functions for FastAPI integration
def get_github_pr_candidate(pr_url: str, github_token: Optional[str] = None) -> Dict[str, Any]:
    """
    Convenience function for FastAPI integration.

    Args:
        pr_url: GitHub PR URL
        github_token: Optional GitHub token

    Returns:
        Standardized candidate format
    """
    generator = GitHubCandidateGenerator(github_token)
    return generator.get_pr_candidate(pr_url)


def get_github_repo_candidates(owner: str, repo: str, github_token: Optional[str] = None,
                              state: str = 'open', limit: int = 10) -> List[Dict[str, Any]]:
    """
    Get PR candidates from a specific repository.

    Args:
        owner: Repository owner
        repo: Repository name
        github_token: Optional GitHub token
        state: PR state ('open', 'closed', 'all')
        limit: Maximum number of PRs to fetch

    Returns:
        List of standardized candidates
    """
    generator = GitHubCandidateGenerator(github_token)
    return generator.fetch_repo_prs(owner, repo, state, limit)


def get_github_user_candidates(username: str, github_token: Optional[str] = None,
                              state: str = 'open', limit: int = 20) -> List[Dict[str, Any]]:
    """
    Get PR candidates for a specific user.

    Args:
        username: GitHub username
        github_token: Optional GitHub token
        state: PR state ('open', 'closed', 'all')
        limit: Maximum number of PRs to fetch

    Returns:
        List of standardized candidates
    """
    generator = GitHubCandidateGenerator(github_token)
    return generator.fetch_user_prs(username, state, limit)


github_token = os.getenv('GITHUB_TOKEN')
res = get_github_user_candidates('moht-agrawal-rubrik', github_token)
print(json.dumps(res, indent=2))

