"""
GitHub Candidate Generator Package

This package contains all GitHub-related functionality for the candidate generation system.
It processes GitHub Pull Requests and converts them into the standardized candidate format
as defined in guidelines.md.

Main Components:
- GitHubCandidateGenerator: Main class for fetching and processing GitHub PRs
- PRProcessor: Core processing engine for converting raw PR data to guidelines.md format
- Scoring Algorithm: Sophisticated urgency scoring based on time, reviewers, and comments
- Action Items Generation: Intelligent extraction of actionable items from PR data

Usage:
    from github.github_candidate_generator import GitHubCandidateGenerator
    from github.pr_processor import process_github_pr_data
    
    # Initialize generator
    generator = GitHubCandidateGenerator(github_token)
    
    # Process a single PR
    result = generator.get_pr_candidate(pr_url)
    
    # Or process raw data directly
    processed = process_github_pr_data(raw_pr_data)
"""

from .github_candidate_generator import GitHubCandidateGenerator
from .pr_processor import PRProcessor, process_github_pr_data

__version__ = "1.0.0"
__author__ = "GitHub Candidate Generator Team"

__all__ = [
    "GitHubCandidateGenerator",
    "PRProcessor", 
    "process_github_pr_data"
]
