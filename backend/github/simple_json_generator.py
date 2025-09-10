#!/usr/bin/env python3
"""
Simple JSON Generator using GitHub Candidate Generator

A simplified script that demonstrates basic usage of the GitHubCandidateGenerator
to fetch and output JSON data for GitHub PRs.
"""

import os
import json
from dotenv import load_dotenv
from github_candidate_generator import GitHubCandidateGenerator

# Load environment variables
load_dotenv()


def main():
    """
    Simple example of generating JSON data from GitHub PRs.
    """
    # Get GitHub token from environment
    github_token = os.getenv('GITHUB_TOKEN')
    if not github_token:
        print("Error: GITHUB_TOKEN environment variable is required")
        return
    
    # Initialize the generator
    generator = GitHubCandidateGenerator(github_token)
    
    print("GitHub JSON Data Generator")
    print("=" * 40)
    
    # Example 1: Get PRs for a specific user
    print("\n1. Fetching PRs for user 'moht-agrawal-rubrik'...")
    try:
        user_candidates = generator.fetch_user_prs("moht-agrawal-rubrik", limit=2)
        print(f"Found {len(user_candidates)} PRs")
        
        # Save to file
        with open("user_prs_simple.json", "w") as f:
            json.dump(user_candidates, f, indent=2)
        print("Saved to: user_prs_simple.json")
        
        # Show summary of each PR
        for candidate in user_candidates:
            raw_data = candidate.get("raw_data", {})
            processed_data = candidate.get("processed_data", {})
            
            print(f"\nPR #{raw_data.get('metadata', {}).get('number', 'Unknown')}")
            print(f"Title: {raw_data.get('pr_title', 'No title')}")
            print(f"URL: {raw_data.get('pr_url', 'No URL')}")
            print(f"Score: {processed_data.get('score', 'No score')}")
            print(f"Action Items: {processed_data.get('action_items', [])}")
            
    except Exception as e:
        print(f"Error fetching user PRs: {e}")
    
    # Example 2: Get a specific PR by URL (commented out - replace with real PR URL)
    print("\n2. Example of fetching a specific PR by URL:")
    print("# Uncomment and replace with a real PR URL to test:")
    print("# pr_url = 'https://github.com/owner/repo/pull/123'")
    print("# candidate = generator.get_pr_candidate(pr_url)")
    print("# print(json.dumps(candidate, indent=2))")
    
    # Example 3: Get repository PRs (commented out - replace with real repo)
    print("\n3. Example of fetching repository PRs:")
    print("# Uncomment and replace with a real repository to test:")
    print("# repo_candidates = generator.fetch_repo_prs('owner', 'repo', limit=3)")
    print("# print(f'Found {len(repo_candidates)} repository PRs')")
    
    print("\nDone! Check the generated JSON files for detailed data.")


if __name__ == "__main__":
    main()
