#!/usr/bin/env python3
"""
JSON Data Generator using GitHub Candidate Generator

This script demonstrates how to use the GitHubCandidateGenerator to fetch
and process GitHub PR data, outputting structured JSON data.
"""

import os
import json
import sys
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import the GitHub candidate generator
from github_candidate_generator import GitHubCandidateGenerator


def generate_single_pr_json(pr_url: str, output_file: Optional[str] = None) -> Dict[str, Any]:
    """
    Generate JSON data for a single GitHub PR.
    
    Args:
        pr_url: GitHub PR URL
        output_file: Optional file path to save JSON output
        
    Returns:
        Dictionary containing the processed PR data
    """
    github_token = os.getenv('GITHUB_TOKEN')
    if not github_token:
        raise ValueError("GITHUB_TOKEN environment variable is required")
    
    generator = GitHubCandidateGenerator(github_token)
    
    try:
        # Get the candidate data
        candidate_data = generator.get_pr_candidate(pr_url)
        
        # Pretty print to console
        print(f"Generated JSON data for PR: {pr_url}")
        print("=" * 60)
        print(json.dumps(candidate_data, indent=2))
        
        # Save to file if specified
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(candidate_data, f, indent=2)
            print(f"\nJSON data saved to: {output_file}")
        
        return candidate_data
        
    except Exception as e:
        print(f"Error processing PR {pr_url}: {e}")
        return {}


def generate_repo_prs_json(owner: str, repo: str, limit: int = 5, 
                          output_file: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Generate JSON data for multiple PRs from a repository.
    
    Args:
        owner: Repository owner
        repo: Repository name
        limit: Maximum number of PRs to fetch
        output_file: Optional file path to save JSON output
        
    Returns:
        List of processed PR candidates
    """
    github_token = os.getenv('GITHUB_TOKEN')
    if not github_token:
        raise ValueError("GITHUB_TOKEN environment variable is required")
    
    generator = GitHubCandidateGenerator(github_token)
    
    try:
        # Get repository PR candidates
        candidates = generator.fetch_repo_prs(owner, repo, state='open', limit=limit)
        
        # Pretty print to console
        print(f"Generated JSON data for {len(candidates)} PRs from {owner}/{repo}")
        print("=" * 60)
        print(json.dumps(candidates, indent=2))
        
        # Save to file if specified
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(candidates, f, indent=2)
            print(f"\nJSON data saved to: {output_file}")
        
        return candidates
        
    except Exception as e:
        print(f"Error processing repository {owner}/{repo}: {e}")
        return []


def generate_user_prs_json(username: str, limit: int = 10, 
                          output_file: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Generate JSON data for PRs associated with a specific user.
    
    Args:
        username: GitHub username
        limit: Maximum number of PRs to fetch
        output_file: Optional file path to save JSON output
        
    Returns:
        List of processed PR candidates
    """
    github_token = os.getenv('GITHUB_TOKEN')
    if not github_token:
        raise ValueError("GITHUB_TOKEN environment variable is required")
    
    generator = GitHubCandidateGenerator(github_token)
    
    try:
        # Get user PR candidates
        candidates = generator.fetch_user_prs(username, state='open', limit=limit)
        
        # Pretty print to console
        print(f"Generated JSON data for {len(candidates)} PRs for user: {username}")
        print("=" * 60)
        print(json.dumps(candidates, indent=2))
        
        # Save to file if specified
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(candidates, f, indent=2)
            print(f"\nJSON data saved to: {output_file}")
        
        return candidates
        
    except Exception as e:
        print(f"Error processing user {username}: {e}")
        return []


def generate_multiple_prs_json(pr_urls: List[str], 
                              output_file: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Generate JSON data for multiple specific PRs.
    
    Args:
        pr_urls: List of GitHub PR URLs
        output_file: Optional file path to save JSON output
        
    Returns:
        List of processed PR candidates
    """
    github_token = os.getenv('GITHUB_TOKEN')
    if not github_token:
        raise ValueError("GITHUB_TOKEN environment variable is required")
    
    generator = GitHubCandidateGenerator(github_token)
    
    try:
        # Get multiple PR candidates
        candidates = generator.get_pr_candidates(pr_urls)
        
        # Pretty print to console
        print(f"Generated JSON data for {len(candidates)} PRs")
        print("=" * 60)
        print(json.dumps(candidates, indent=2))
        
        # Save to file if specified
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(candidates, f, indent=2)
            print(f"\nJSON data saved to: {output_file}")
        
        return candidates
        
    except Exception as e:
        print(f"Error processing multiple PRs: {e}")
        return []


def main():
    """
    Main function demonstrating different ways to generate JSON data.
    """
    print("GitHub Candidate Generator - JSON Data Examples")
    print("=" * 60)
    
    # Example 1: Single PR
    print("\n1. Single PR Example:")
    single_pr_url = "https://github.com/octocat/Hello-World/pull/1"
    # Uncomment to test with a real PR:
    # generate_single_pr_json(single_pr_url, "single_pr_output.json")
    
    # Example 2: Repository PRs
    print("\n2. Repository PRs Example:")
    # Uncomment to test with a real repository:
    # generate_repo_prs_json("octocat", "Hello-World", limit=3, output_file="repo_prs_output.json")
    
    # Example 3: User PRs (using the existing code from the generator)
    print("\n3. User PRs Example:")
    try:
        candidates = generate_user_prs_json("moht-agrawal-rubrik", limit=5, output_file="user_prs_output.json")
        print(f"Successfully generated data for {len(candidates)} PRs")
    except Exception as e:
        print(f"Error in user PRs example: {e}")
    
    # Example 4: Multiple specific PRs
    print("\n4. Multiple PRs Example:")
    example_pr_urls = [
        "https://github.com/octocat/Hello-World/pull/1",
        "https://github.com/octocat/Hello-World/pull/2"
    ]
    # Uncomment to test with real PRs:
    # generate_multiple_prs_json(example_pr_urls, "multiple_prs_output.json")
    
    print("\nJSON generation examples completed!")


if __name__ == "__main__":
    main()
