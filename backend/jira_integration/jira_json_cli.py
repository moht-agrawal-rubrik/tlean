#!/usr/bin/env python3
"""
Command-line interface for JIRA JSON output functionality.
"""

import argparse
import json
import sys
import importlib.util
from typing import List, Dict, Any


def load_jira_module():
    """Load the jira-main module."""
    try:
        spec = importlib.util.spec_from_file_location("jira_main", "jira-main.py")
        jira_main = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(jira_main)
        return jira_main
    except Exception as e:
        print(f"❌ Error loading JIRA module: {e}")
        sys.exit(1)


def format_output(results: List[Dict[str, Any]], format_type: str = "json") -> str:
    """Format the results for output."""
    if format_type == "json":
        return json.dumps(results, indent=2, ensure_ascii=False)
    elif format_type == "summary":
        output = []
        output.append(f"📋 JIRA Issues Summary ({len(results)} issues)")
        output.append("=" * 50)
        
        for i, item in enumerate(results, 1):
            output.append(f"\n{i}. {item['title']}")
            output.append(f"   🔗 {item['link']}")
            output.append(f"   📊 Score: {item['score']}")
            output.append(f"   ⏰ Updated: {item['timestamp']}")
            output.append(f"   ✅ Actions: {len(item['action_items'])}")
            
            if item['action_items']:
                for j, action in enumerate(item['action_items'], 1):
                    output.append(f"      {j}. {action}")
        
        return "\n".join(output)
    else:
        return json.dumps(results, indent=2)


def filter_results(results: List[Dict[str, Any]], min_score: float = None, 
                  max_results: int = None) -> List[Dict[str, Any]]:
    """Filter and limit results based on criteria."""
    filtered = results
    
    # Filter by minimum score
    if min_score is not None:
        filtered = [item for item in filtered if item['score'] >= min_score]
    
    # Sort by score (highest first)
    filtered.sort(key=lambda x: x['score'], reverse=True)
    
    # Limit number of results
    if max_results is not None:
        filtered = filtered[:max_results]
    
    return filtered


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="Generate JSON output for JIRA issues",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                          # Get open assigned issues (max 10)
  %(prog)s --keys CDM-123 CDM-456   # Process specific issues
  %(prog)s --min-score 0.7          # Only high-urgency issues
  %(prog)s --format summary          # Human-readable summary
  %(prog)s --output results.json     # Save to file
  %(prog)s --limit 5                # Limit to 5 results
        """
    )
    
    parser.add_argument(
        '--keys', 
        nargs='+', 
        help='Specific JIRA issue keys to process (e.g., CDM-123 CDM-456)'
    )
    
    parser.add_argument(
        '--min-score', 
        type=float, 
        help='Minimum urgency score (0.0 to 1.0)'
    )
    
    parser.add_argument(
        '--limit',
        type=int,
        help='Maximum number of results to return (applied after JIRA query limit of 10)'
    )
    
    parser.add_argument(
        '--format', 
        choices=['json', 'summary'], 
        default='json',
        help='Output format (default: json)'
    )
    
    parser.add_argument(
        '--output', 
        help='Output file path (default: stdout)'
    )
    
    parser.add_argument(
        '--quiet', 
        action='store_true',
        help='Suppress progress messages'
    )
    
    args = parser.parse_args()
    
    # Load JIRA module
    if not args.quiet:
        print("🔍 Loading JIRA module...", file=sys.stderr)
    
    jira_main = load_jira_module()
    
    try:
        # Get results
        if args.keys:
            if not args.quiet:
                print(f"📋 Processing {len(args.keys)} specific JIRA issues...", file=sys.stderr)
            processor = jira_main.JiraJSONProcessor()
            results = processor.convert_jira_to_json(args.keys)
        else:
            if not args.quiet:
                print("📋 Fetching open assigned JIRA issues (max 10)...", file=sys.stderr)
            results = jira_main.generate_jira_json_output()
        
        if not results:
            print("❌ No JIRA issues found or processed.", file=sys.stderr)
            sys.exit(1)
        
        # Filter results
        filtered_results = filter_results(
            results, 
            min_score=args.min_score, 
            max_results=args.limit
        )
        
        if not args.quiet:
            print(f"✅ Found {len(results)} issues, showing {len(filtered_results)} after filtering", file=sys.stderr)
        
        # Format output
        output = format_output(filtered_results, args.format)
        
        # Write output
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(output)
            if not args.quiet:
                print(f"💾 Results saved to: {args.output}", file=sys.stderr)
        else:
            print(output)
    
    except KeyboardInterrupt:
        print("\n❌ Operation cancelled by user.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
