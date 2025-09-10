#!/usr/bin/env python3
"""
GitHub Pull Request Scraper
Scrapes a GitHub pull request and saves all information to a markdown file.
"""

import os
import re
import json
import argparse
from datetime import datetime
from typing import Dict, List, Optional, Any
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class GitHubPRScraper:
    """Scrapes GitHub Pull Requests and converts them to Markdown."""
    
    def __init__(self, github_token: Optional[str] = None):
        """
        Initialize the scraper with optional GitHub token for higher rate limits.
        
        Args:
            github_token: GitHub personal access token (optional)
        """
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'GitHub-PR-Scraper/1.0'
        })
        
        if github_token:
            self.session.headers['Authorization'] = f'token {github_token}'
        
        self.base_url = 'https://api.github.com'
    
    def parse_pr_url(self, url: str) -> tuple:
        """
        Parse GitHub PR URL to extract owner, repo, and PR number.
        
        Args:
            url: GitHub PR URL
            
        Returns:
            Tuple of (owner, repo, pr_number)
        """
        # Handle both PR URLs and API URLs
        patterns = [
            r'github\.com/([^/]+)/([^/]+)/pull/(\d+)',
            r'api\.github\.com/repos/([^/]+)/([^/]+)/pulls/(\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1), match.group(2), int(match.group(3))
        
        raise ValueError(f"Invalid GitHub PR URL: {url}")
    
    def get_pr_data(self, owner: str, repo: str, pr_number: int) -> Dict[str, Any]:
        """
        Fetch pull request data from GitHub API.
        
        Args:
            owner: Repository owner
            repo: Repository name
            pr_number: Pull request number
            
        Returns:
            Dictionary containing PR data
        """
        pr_url = f"{self.base_url}/repos/{owner}/{repo}/pulls/{pr_number}"
        
        print(f"Fetching PR data from: {pr_url}")
        response = self.session.get(pr_url)
        response.raise_for_status()
        
        return response.json()
    
    def get_pr_commits(self, owner: str, repo: str, pr_number: int) -> List[Dict]:
        """
        Fetch commits associated with the PR.
        
        Args:
            owner: Repository owner
            repo: Repository name
            pr_number: Pull request number
            
        Returns:
            List of commit data
        """
        commits_url = f"{self.base_url}/repos/{owner}/{repo}/pulls/{pr_number}/commits"
        
        print(f"Fetching commits...")
        response = self.session.get(commits_url)
        response.raise_for_status()
        
        return response.json()
    
    def get_pr_comments(self, owner: str, repo: str, pr_number: int) -> List[Dict]:
        """
        Fetch comments on the PR.
        
        Args:
            owner: Repository owner
            repo: Repository name
            pr_number: Pull request number
            
        Returns:
            List of comment data
        """
        # Get issue comments
        issue_comments_url = f"{self.base_url}/repos/{owner}/{repo}/issues/{pr_number}/comments"
        print(f"Fetching issue comments...")
        response = self.session.get(issue_comments_url)
        response.raise_for_status()
        issue_comments = response.json()
        
        # Get review comments
        review_comments_url = f"{self.base_url}/repos/{owner}/{repo}/pulls/{pr_number}/comments"
        print(f"Fetching review comments...")
        response = self.session.get(review_comments_url)
        response.raise_for_status()
        review_comments = response.json()
        
        return issue_comments, review_comments
    
    def get_pr_reviews(self, owner: str, repo: str, pr_number: int) -> List[Dict]:
        """
        Fetch reviews on the PR.
        
        Args:
            owner: Repository owner
            repo: Repository name
            pr_number: Pull request number
            
        Returns:
            List of review data
        """
        reviews_url = f"{self.base_url}/repos/{owner}/{repo}/pulls/{pr_number}/reviews"
        
        print(f"Fetching reviews...")
        response = self.session.get(reviews_url)
        response.raise_for_status()
        
        return response.json()
    
    def get_pr_files(self, owner: str, repo: str, pr_number: int) -> List[Dict]:
        """
        Fetch files changed in the PR.
        
        Args:
            owner: Repository owner
            repo: Repository name
            pr_number: Pull request number
            
        Returns:
            List of file data
        """
        files_url = f"{self.base_url}/repos/{owner}/{repo}/pulls/{pr_number}/files"
        
        print(f"Fetching changed files...")
        all_files = []
        page = 1
        
        while True:
            response = self.session.get(files_url, params={'page': page, 'per_page': 100})
            response.raise_for_status()
            files = response.json()
            
            if not files:
                break
                
            all_files.extend(files)
            page += 1
            
            # Check if there are more pages
            if 'Link' not in response.headers or 'rel="next"' not in response.headers['Link']:
                break
        
        return all_files
    
    def format_user(self, user: Optional[Dict]) -> str:
        """Format user information."""
        if not user:
            return "Unknown"
        return f"[{user.get('login', 'Unknown')}]({user.get('html_url', '#')})"
    
    def format_datetime(self, dt_string: Optional[str]) -> str:
        """Format datetime string."""
        if not dt_string:
            return "Unknown"
        try:
            dt = datetime.fromisoformat(dt_string.replace('Z', '+00:00'))
            return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
        except:
            return dt_string
    
    def generate_markdown(self, pr_data: Dict, commits: List[Dict], 
                         issue_comments: List[Dict], review_comments: List[Dict],
                         reviews: List[Dict], files: List[Dict]) -> str:
        """
        Generate markdown content from PR data.
        
        Args:
            pr_data: Pull request data
            commits: List of commits
            issue_comments: List of issue comments
            review_comments: List of review comments
            reviews: List of reviews
            files: List of changed files
            
        Returns:
            Markdown formatted string
        """
        md_lines = []
        
        # Header
        md_lines.append(f"# Pull Request #{pr_data['number']}: {pr_data['title']}")
        md_lines.append("")
        
        # Metadata
        md_lines.append("## Metadata")
        md_lines.append("")
        md_lines.append(f"- **URL**: {pr_data['html_url']}")
        md_lines.append(f"- **Author**: {self.format_user(pr_data['user'])}")
        md_lines.append(f"- **State**: {pr_data['state']}")
        md_lines.append(f"- **Created**: {self.format_datetime(pr_data['created_at'])}")
        md_lines.append(f"- **Updated**: {self.format_datetime(pr_data['updated_at'])}")
        if pr_data.get('merged_at'):
            md_lines.append(f"- **Merged**: {self.format_datetime(pr_data['merged_at'])}")
            md_lines.append(f"- **Merged By**: {self.format_user(pr_data.get('merged_by'))}")
        if pr_data.get('closed_at'):
            md_lines.append(f"- **Closed**: {self.format_datetime(pr_data['closed_at'])}")
        md_lines.append(f"- **Base Branch**: `{pr_data['base']['ref']}`")
        md_lines.append(f"- **Head Branch**: `{pr_data['head']['ref']}`")
        
        # Labels
        if pr_data.get('labels'):
            labels = ', '.join([f"`{label['name']}`" for label in pr_data['labels']])
            md_lines.append(f"- **Labels**: {labels}")
        
        # Assignees
        if pr_data.get('assignees'):
            assignees = ', '.join([self.format_user(user) for user in pr_data['assignees']])
            md_lines.append(f"- **Assignees**: {assignees}")
        
        # Reviewers
        if pr_data.get('requested_reviewers'):
            reviewers = ', '.join([self.format_user(user) for user in pr_data['requested_reviewers']])
            md_lines.append(f"- **Requested Reviewers**: {reviewers}")
        
        md_lines.append("")
        
        # Description
        md_lines.append("## Description")
        md_lines.append("")
        if pr_data.get('body'):
            md_lines.append(pr_data['body'])
        else:
            md_lines.append("*No description provided.*")
        md_lines.append("")
        
        # Stats
        md_lines.append("## Statistics")
        md_lines.append("")
        md_lines.append(f"- **Commits**: {pr_data.get('commits', 0)}")
        md_lines.append(f"- **Files Changed**: {pr_data.get('changed_files', 0)}")
        md_lines.append(f"- **Additions**: +{pr_data.get('additions', 0)}")
        md_lines.append(f"- **Deletions**: -{pr_data.get('deletions', 0)}")
        md_lines.append(f"- **Total Comments**: {pr_data.get('comments', 0)}")
        md_lines.append(f"- **Review Comments**: {pr_data.get('review_comments', 0)}")
        md_lines.append("")
        
        # Commits
        if commits:
            md_lines.append("## Commits")
            md_lines.append("")
            for commit in commits:
                sha_short = commit['sha'][:7]
                author = commit['commit']['author']['name']
                date = self.format_datetime(commit['commit']['author']['date'])
                message = commit['commit']['message'].split('\n')[0]  # First line only
                md_lines.append(f"- `{sha_short}` - {message} ({author}, {date})")
            md_lines.append("")
        
        # Files Changed
        if files:
            md_lines.append("## Files Changed")
            md_lines.append("")
            
            for file in files:
                status_emoji = {
                    'added': '✨',
                    'removed': '🗑️',
                    'modified': '📝',
                    'renamed': '📋'
                }.get(file['status'], '📄')
                
                md_lines.append(f"### {status_emoji} {file['filename']}")
                md_lines.append("")
                md_lines.append(f"- **Status**: {file['status']}")
                md_lines.append(f"- **Additions**: +{file['additions']}")
                md_lines.append(f"- **Deletions**: -{file['deletions']}")
                md_lines.append(f"- **Changes**: {file['changes']}")
                
                if file.get('patch'):
                    md_lines.append("")
                    md_lines.append("```diff")
                    md_lines.append(file['patch'])
                    md_lines.append("```")
                
                md_lines.append("")
        
        # Reviews
        if reviews:
            md_lines.append("## Reviews")
            md_lines.append("")
            
            for review in reviews:
                reviewer = self.format_user(review['user'])
                state = review['state'].replace('_', ' ').title()
                date = self.format_datetime(review['submitted_at'])
                
                md_lines.append(f"### Review by {reviewer}")
                md_lines.append(f"- **State**: {state}")
                md_lines.append(f"- **Submitted**: {date}")
                
                if review.get('body'):
                    md_lines.append("")
                    md_lines.append(review['body'])
                
                md_lines.append("")
        
        # Issue Comments
        if issue_comments:
            md_lines.append("## Discussion Comments")
            md_lines.append("")
            
            for comment in issue_comments:
                author = self.format_user(comment['user'])
                date = self.format_datetime(comment['created_at'])
                
                md_lines.append(f"### Comment by {author} on {date}")
                md_lines.append("")
                md_lines.append(comment['body'])
                md_lines.append("")
        
        # Review Comments (inline code comments)
        if review_comments:
            md_lines.append("## Code Review Comments")
            md_lines.append("")
            
            for comment in review_comments:
                author = self.format_user(comment['user'])
                date = self.format_datetime(comment['created_at'])
                path = comment.get('path', 'Unknown file')
                line = comment.get('line') or comment.get('original_line', 'Unknown')
                
                md_lines.append(f"### Comment by {author} on {date}")
                md_lines.append(f"- **File**: `{path}`")
                md_lines.append(f"- **Line**: {line}")
                
                if comment.get('diff_hunk'):
                    md_lines.append("")
                    md_lines.append("```diff")
                    md_lines.append(comment['diff_hunk'])
                    md_lines.append("```")
                
                md_lines.append("")
                md_lines.append(comment['body'])
                md_lines.append("")
        
        # Footer
        md_lines.append("---")
        md_lines.append("")
        md_lines.append(f"*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
        
        return '\n'.join(md_lines)
    
    def scrape_pr(self, pr_url: str, output_file: Optional[str] = None) -> str:
        """
        Scrape a GitHub pull request and save to markdown file.
        
        Args:
            pr_url: GitHub PR URL
            output_file: Output file path (optional, auto-generated if not provided)
            
        Returns:
            Path to the generated markdown file
        """
        # Parse PR URL
        owner, repo, pr_number = self.parse_pr_url(pr_url)
        
        print(f"Scraping PR #{pr_number} from {owner}/{repo}...")
        
        try:
            # Fetch all PR data
            pr_data = self.get_pr_data(owner, repo, pr_number)
            commits = self.get_pr_commits(owner, repo, pr_number)
            issue_comments, review_comments = self.get_pr_comments(owner, repo, pr_number)
            reviews = self.get_pr_reviews(owner, repo, pr_number)
            files = self.get_pr_files(owner, repo, pr_number)
            
            # Generate markdown
            print("Generating markdown...")
            markdown_content = self.generate_markdown(
                pr_data, commits, issue_comments, 
                review_comments, reviews, files
            )
            
            # Determine output file name
            if not output_file:
                # Create a safe filename
                safe_title = re.sub(r'[^a-zA-Z0-9_-]', '_', pr_data['title'][:50])
                output_file = f"PR_{pr_number}_{safe_title}.md"
            
            # Write to file
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            print(f"✅ Successfully saved PR to: {output_file}")
            return output_file
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                raise ValueError(f"PR not found: {pr_url}")
            elif e.response.status_code == 403:
                raise ValueError("Rate limit exceeded. Please provide a GitHub token.")
            else:
                raise
        except Exception as e:
            raise Exception(f"Failed to scrape PR: {str(e)}")


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description='Scrape GitHub Pull Requests and save as Markdown files'
    )
    parser.add_argument(
        'url',
        help='GitHub PR URL (e.g., https://github.com/owner/repo/pull/123)'
    )
    parser.add_argument(
        '-o', '--output',
        help='Output file path (optional, auto-generated if not provided)'
    )
    parser.add_argument(
        '-t', '--token',
        help='GitHub personal access token (can also be set via GITHUB_TOKEN env var)'
    )
    parser.add_argument(
        '--include-patches',
        action='store_true',
        help='Include full patch diffs in the output (can make files very large)'
    )
    
    args = parser.parse_args()
    
    # Get GitHub token
    github_token = args.token or os.getenv('GITHUB_TOKEN')
    
    if not github_token:
        print("⚠️  Warning: No GitHub token provided. You may hit rate limits.")
        print("   Set GITHUB_TOKEN environment variable or use --token flag.")
        print()
    
    # Create scraper and run
    scraper = GitHubPRScraper(github_token)
    
    try:
        output_path = scraper.scrape_pr(args.url, args.output)
        print(f"\n📄 Markdown file created: {output_path}")
        
        # Show file size
        file_size = os.path.getsize(output_path)
        if file_size > 1024 * 1024:
            print(f"   File size: {file_size / (1024 * 1024):.2f} MB")
        else:
            print(f"   File size: {file_size / 1024:.2f} KB")
            
    except ValueError as e:
        print(f"❌ Error: {e}")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())

