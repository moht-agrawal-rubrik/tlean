"""
LLM-powered diff analysis and action item generation for GitHub PRs.

This module provides intelligent analysis of code diffs using LLM to generate
concise summaries and identify potential code quality issues. It also includes
action item generation from PR comments using LLM analysis.
"""

import os
import re
import json
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

try:
    from openai import OpenAI
    from dotenv import load_dotenv
    load_dotenv()
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


@dataclass
class FileDiffSummary:
    """Summary of changes for a single file."""
    filename: str
    summary: str  # <200 chars
    quality_issues: List[str]  # Only serious issues, empty list preferred
    lines_added: int
    lines_removed: int
    is_auto_generated: bool


@dataclass
class DiffAnalysis:
    """Complete diff analysis for a PR."""
    file_summaries: List[FileDiffSummary]
    overall_summary: str
    total_files_changed: int
    total_lines_added: int
    total_lines_removed: int


class DiffAnalyzer:
    """Analyzes PR diffs using LLM to generate intelligent summaries."""

    # File patterns that are typically auto-generated
    AUTO_GENERATED_PATTERNS = [
        r'\.pb\.py$',  # Protocol buffer files
        r'\.pb\.go$',
        r'\.pb\.h$',
        r'\.pb\.cc$',
        r'package-lock\.json$',
        r'yarn\.lock$',
        r'Cargo\.lock$',
        r'go\.sum$',
        r'\.min\.js$',
        r'\.min\.css$',
        r'dist/',
        r'build/',
        r'target/',
        r'node_modules/',
        r'__pycache__/',
        r'\.pyc$',
        r'\.class$',
        r'\.o$',
        r'\.so$',
        r'\.dll$',
        r'\.exe$',
    ]

    # Thresholds for diff analysis
    MAX_DIFF_SIZE_PER_FILE = 5000  # chars
    MAX_FILES_TO_ANALYZE = 20
    MAX_SUMMARY_LENGTH = 180  # chars per file

    def __init__(self, use_openai: bool = True):
        """
        Initialize the diff analyzer.

        Args:
            use_openai: Whether to use OpenAI for LLM analysis
        """
        self.use_openai = use_openai and OPENAI_AVAILABLE
        self.openai_client = None

        if self.use_openai:
            try:
                self.openai_client = OpenAI(
                    api_key=os.environ.get("OPENAI_API_KEY"),
                    base_url="https://basecamp.stark.rubrik.com"
                )
            except Exception as e:
                print(f"Warning: Failed to initialize OpenAI client: {e}")
                self.use_openai = False
    
    def analyze_pr_diff(self, pr_data: Dict[str, Any]) -> DiffAnalysis:
        """
        Analyze the complete PR diff and generate intelligent summaries.
        
        Args:
            pr_data: PR data containing diff information
            
        Returns:
            DiffAnalysis with file-by-file summaries and overall analysis
        """
        # Extract diff data from PR
        diff_data = self._extract_diff_data(pr_data)
        
        if not diff_data:
            return self._create_fallback_analysis(pr_data)
        
        # Filter and prioritize files for analysis
        files_to_analyze = self._filter_files_for_analysis(diff_data)
        
        # Analyze each file
        file_summaries = []
        for file_info in files_to_analyze:
            summary = self._analyze_single_file(file_info)
            if summary:
                file_summaries.append(summary)
        
        # Generate overall summary
        overall_summary = self._generate_overall_summary(file_summaries, pr_data)
        
        # Calculate totals
        total_files = len(diff_data)
        total_added = sum(f.get('lines_added', 0) for f in diff_data)
        total_removed = sum(f.get('lines_removed', 0) for f in diff_data)
        
        return DiffAnalysis(
            file_summaries=file_summaries,
            overall_summary=overall_summary,
            total_files_changed=total_files,
            total_lines_added=total_added,
            total_lines_removed=total_removed
        )
    
    def _extract_diff_data(self, pr_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract diff data from PR data structure."""
        # Check if diff data exists in the PR data (test format)
        diff_data = pr_data.get('diff_data', [])
        if diff_data:
            return diff_data

        # Check for GitHub API format (files_changed with patch data)
        files_changed = pr_data.get('files_changed', [])
        if files_changed:
            extracted_files = []
            for file_info in files_changed:
                # Convert GitHub API format to our internal format
                extracted_files.append({
                    'filename': file_info.get('filename', ''),
                    'lines_added': file_info.get('additions', 0),
                    'lines_removed': file_info.get('deletions', 0),
                    'diff': file_info.get('patch', '')  # GitHub API provides patch as diff
                })
            return extracted_files

        # Fallback: Try to extract from statistics (creates empty diffs)
        stats = pr_data.get('statistics', {})
        if stats.get('files_changed'):
            # Create minimal file info from statistics
            return [{
                'filename': f'file_{i}',
                'lines_added': stats.get('additions', 0) // stats.get('files_changed', 1),
                'lines_removed': stats.get('deletions', 0) // stats.get('files_changed', 1),
                'diff': ''
            } for i in range(stats.get('files_changed', 0))]

        return []
    
    def _filter_files_for_analysis(self, diff_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter and prioritize files for LLM analysis."""
        filtered_files = []
        
        for file_info in diff_data:
            filename = file_info.get('filename', '')
            diff_content = file_info.get('diff', '')
            
            # Skip auto-generated files
            if self._is_auto_generated(filename):
                continue
            
            # Skip files with very large diffs
            if len(diff_content) > self.MAX_DIFF_SIZE_PER_FILE:
                continue
            
            # Skip empty diffs
            if not diff_content.strip():
                continue
            
            filtered_files.append(file_info)
        
        # Sort by importance (smaller diffs first, then by file type)
        filtered_files.sort(key=lambda f: (
            len(f.get('diff', '')),
            not self._is_important_file_type(f.get('filename', ''))
        ))
        
        # Limit number of files to analyze
        return filtered_files[:self.MAX_FILES_TO_ANALYZE]
    
    def _is_auto_generated(self, filename: str) -> bool:
        """Check if a file is likely auto-generated."""
        return any(re.search(pattern, filename, re.IGNORECASE) 
                  for pattern in self.AUTO_GENERATED_PATTERNS)
    
    def _is_important_file_type(self, filename: str) -> bool:
        """Check if a file type is important for analysis."""
        important_extensions = ['.py', '.js', '.ts', '.java', '.cpp', '.c', '.h', '.go', '.rs', '.rb']
        return any(filename.endswith(ext) for ext in important_extensions)
    
    def _analyze_single_file(self, file_info: Dict[str, Any]) -> Optional[FileDiffSummary]:
        """Analyze a single file's diff using LLM or heuristics."""
        filename = file_info.get('filename', '')
        diff_content = file_info.get('diff', '')
        lines_added = file_info.get('lines_added', 0)
        lines_removed = file_info.get('lines_removed', 0)

        if not diff_content.strip():
            return None

        # Use OpenAI LLM if available, otherwise use heuristic analysis
        if self.use_openai and self.openai_client:
            return self._openai_analyze_file(filename, diff_content, lines_added, lines_removed)
        else:
            return self._heuristic_analyze_file(filename, diff_content, lines_added, lines_removed)
    
    def _openai_analyze_file(self, filename: str, diff_content: str, lines_added: int, lines_removed: int) -> FileDiffSummary:
        """Analyze file using OpenAI LLM."""
        try:
            # Create system prompt for diff analysis
            system_prompt = self._create_diff_analysis_prompt()

            # Create user prompt with the diff
            user_prompt = self._create_user_prompt(filename, diff_content, lines_added, lines_removed)

            # Call OpenAI API
            response = self.openai_client.chat.completions.create(
                model="gpt-4.1",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,  # Low temperature for consistent, focused output
                max_tokens=200    # Limit response length
            )

            # Parse the response
            llm_response = response.choices[0].message.content.strip()
            summary, quality_issues = self._parse_llm_response(llm_response)

            return FileDiffSummary(
                filename=filename,
                summary=summary,
                quality_issues=quality_issues,
                lines_added=lines_added,
                lines_removed=lines_removed,
                is_auto_generated=self._is_auto_generated(filename)
            )

        except Exception as e:
            print(f"Warning: OpenAI analysis failed for {filename}: {e}")
            # Fall back to heuristic analysis
            return self._heuristic_analyze_file(filename, diff_content, lines_added, lines_removed)

    def _create_diff_analysis_prompt(self) -> str:
        """Create system prompt for diff analysis."""
        return """You are a code review expert. Analyze git diffs and provide concise summaries.

REQUIREMENTS:
1. Generate a 1-2 line summary (max 180 chars) describing what actually changed in the code
2. Focus on functional changes, not formatting or comments
3. Use point format: "Added X, Modified Y, Removed Z"
4. Be specific about what was added/changed (functions, classes, logic, etc.)
5. Only flag SERIOUS code quality issues (hardcoded secrets, SQL injection, dangerous eval)
6. Prefer empty quality issues list over false positives

OUTPUT FORMAT:
SUMMARY: [1-2 line description of changes]
ISSUES: [comma-separated list of serious issues, or "none"]

EXAMPLES:
SUMMARY: Added JWT authentication service with token generation and validation
ISSUES: none

SUMMARY: Modified user permissions logic, added role-based access control
ISSUES: Hardcoded API key detected

Be concise, accurate, and conservative with quality issues."""

    def _create_user_prompt(self, filename: str, diff_content: str, lines_added: int, lines_removed: int) -> str:
        """Create user prompt with diff content."""
        # Truncate diff if too long
        if len(diff_content) > self.MAX_DIFF_SIZE_PER_FILE:
            diff_content = diff_content[:self.MAX_DIFF_SIZE_PER_FILE] + "\n... [truncated]"

        return f"""Analyze this git diff:

FILE: {filename}
CHANGES: +{lines_added}/-{lines_removed} lines

DIFF:
{diff_content}

Provide a concise summary of what actually changed in this file."""

    def _parse_llm_response(self, response: str) -> tuple[str, List[str]]:
        """Parse LLM response into summary and quality issues."""
        summary = ""
        quality_issues = []

        lines = response.strip().split('\n')

        for line in lines:
            line = line.strip()
            if line.startswith('SUMMARY:'):
                summary = line[8:].strip()
            elif line.startswith('ISSUES:'):
                issues_text = line[7:].strip().lower()
                if issues_text and issues_text != 'none':
                    # Split by comma and clean up
                    quality_issues = [issue.strip() for issue in issues_text.split(',') if issue.strip()]

        # Ensure summary length limit
        if len(summary) > self.MAX_SUMMARY_LENGTH:
            summary = summary[:self.MAX_SUMMARY_LENGTH-3] + "..."

        # Fallback if parsing failed
        if not summary:
            summary = f"Modified {filename.split('/')[-1]}"

        return summary, quality_issues

    def _heuristic_analyze_file(self, filename: str, diff_content: str, lines_added: int, lines_removed: int) -> FileDiffSummary:
        """Analyze file using heuristic rules."""
        # Extract meaningful changes from diff
        added_lines = [line[1:] for line in diff_content.split('\n') if line.startswith('+') and not line.startswith('+++')]
        removed_lines = [line[1:] for line in diff_content.split('\n') if line.startswith('-') and not line.startswith('---')]
        
        # Generate summary based on patterns
        summary = self._generate_heuristic_summary(filename, added_lines, removed_lines, lines_added, lines_removed)
        
        # Check for quality issues
        quality_issues = self._detect_quality_issues(added_lines, filename)
        
        return FileDiffSummary(
            filename=filename,
            summary=summary,
            quality_issues=quality_issues,
            lines_added=lines_added,
            lines_removed=lines_removed,
            is_auto_generated=self._is_auto_generated(filename)
        )
    
    def _generate_heuristic_summary(self, filename: str, added_lines: List[str], removed_lines: List[str], lines_added: int, lines_removed: int) -> str:
        """Generate summary using heuristic analysis."""
        # Analyze the type of changes
        change_types = []
        
        # Check for new functions/methods
        new_functions = [line for line in added_lines if re.search(r'def\s+\w+|function\s+\w+|class\s+\w+', line.strip())]
        if new_functions:
            change_types.append("new functions")
        
        # Check for imports/dependencies
        new_imports = [line for line in added_lines if re.search(r'import\s+|from\s+.*import|#include|require\(', line.strip())]
        if new_imports:
            change_types.append("dependencies")
        
        # Check for configuration changes
        config_changes = [line for line in added_lines if re.search(r'config|setting|parameter', line.lower())]
        if config_changes:
            change_types.append("config")
        
        # Check for test additions
        if 'test' in filename.lower() or any('test' in line.lower() for line in added_lines[:5]):
            change_types.append("tests")
        
        # Generate concise summary
        if change_types:
            summary = f"Added {', '.join(change_types[:2])}"
        elif lines_added > lines_removed * 2:
            summary = f"Major additions (+{lines_added})"
        elif lines_removed > lines_added * 2:
            summary = f"Major deletions (-{lines_removed})"
        else:
            summary = f"Modified (+{lines_added}/-{lines_removed})"
        
        # Add file context
        file_ext = filename.split('.')[-1] if '.' in filename else ''
        if file_ext in ['py', 'js', 'java', 'cpp']:
            summary = f"{summary} in {file_ext}"
        
        # Ensure length limit
        if len(summary) > self.MAX_SUMMARY_LENGTH:
            summary = summary[:self.MAX_SUMMARY_LENGTH-3] + "..."
        
        return summary
    
    def _detect_quality_issues(self, added_lines: List[str], filename: str) -> List[str]:
        """Detect serious code quality issues in added lines."""
        issues = []
        
        # Only flag really serious issues to avoid spam
        for line in added_lines[:10]:  # Check only first 10 lines
            line_clean = line.strip().lower()
            
            # Hardcoded credentials (very serious)
            if re.search(r'password\s*=\s*["\'][^"\']+["\']|api_key\s*=\s*["\'][^"\']+["\']', line_clean):
                issues.append("Hardcoded credentials detected")
                break
            
            # SQL injection patterns (serious)
            if re.search(r'execute\s*\(\s*["\'].*%.*["\']|query\s*\(\s*["\'].*\+.*["\']', line_clean):
                issues.append("Potential SQL injection")
                break
            
            # Dangerous eval usage (serious)
            if re.search(r'\beval\s*\(|exec\s*\(', line_clean):
                issues.append("Dangerous eval/exec usage")
                break
        
        return issues[:1]  # Return at most 1 issue to avoid spam
    
    def _generate_overall_summary(self, file_summaries: List[FileDiffSummary], pr_data: Dict[str, Any]) -> str:
        """Generate overall PR summary from file summaries."""
        if not file_summaries:
            return self._create_fallback_summary(pr_data)
        
        # Categorize changes
        total_files = len(file_summaries)
        total_added = sum(f.lines_added for f in file_summaries)
        total_removed = sum(f.lines_removed for f in file_summaries)
        
        # Create concise overall summary
        summary_parts = []
        
        # Add change scale
        if total_files == 1:
            summary_parts.append(f"Modified {file_summaries[0].filename}")
        else:
            summary_parts.append(f"Modified {total_files} files")
        
        # Add change magnitude
        if total_added > 100 or total_removed > 100:
            summary_parts.append(f"(+{total_added}/-{total_removed} lines)")
        
        # Add key change types from file summaries
        change_types = set()
        for fs in file_summaries[:3]:  # Look at top 3 files
            if 'test' in fs.summary.lower():
                change_types.add('tests')
            elif 'config' in fs.summary.lower():
                change_types.add('config')
            elif 'function' in fs.summary.lower():
                change_types.add('logic')
        
        if change_types:
            summary_parts.append(f"- {', '.join(sorted(change_types))}")
        
        # Add quality issues if any
        all_issues = [issue for fs in file_summaries for issue in fs.quality_issues]
        if all_issues:
            summary_parts.append(f"⚠️ {all_issues[0]}")
        
        return ". ".join(summary_parts)
    
    def _create_fallback_analysis(self, pr_data: Dict[str, Any]) -> DiffAnalysis:
        """Create fallback analysis when no diff data is available."""
        stats = pr_data.get('statistics', {})
        
        return DiffAnalysis(
            file_summaries=[],
            overall_summary=self._create_fallback_summary(pr_data),
            total_files_changed=stats.get('files_changed', 0),
            total_lines_added=stats.get('additions', 0),
            total_lines_removed=stats.get('deletions', 0)
        )
    
    def _create_fallback_summary(self, pr_data: Dict[str, Any]) -> str:
        """Create fallback summary from PR metadata."""
        stats = pr_data.get('statistics', {})
        pr_title = pr_data.get('pr_title', '')
        
        if stats:
            files = stats.get('files_changed', 0)
            additions = stats.get('additions', 0)
            deletions = stats.get('deletions', 0)
            
            if files > 0:
                return f"Modified {files} files (+{additions}/-{deletions} lines)"
        
        # Extract from title if available
        if pr_title:
            return f"PR: {pr_title[:100]}..."
        
        return "Code changes (details unavailable)"


@dataclass
class ActionItemAnalysis:
    """Analysis of action items from PR comments."""
    action_items: List[str]
    comment_summary: str
    total_comments_analyzed: int
    pending_responses: int


class ActionItemGenerator:
    """Generates action items from PR comments using LLM analysis."""

    # Bot patterns to filter out automated comments
    BOT_PATTERNS = [
        'rubrik-alfred[bot]',
        'rogers-sail-information[bot]',
        'polaris-jenkins-sails[bot]',
        'rubrik-stark-edith[bot]',
        'SD-111029',  # Automated system account
        '[bot]'  # Generic bot pattern
    ]

    # Thresholds for comment analysis
    MAX_COMMENTS_TO_ANALYZE = 50
    MAX_COMMENT_LENGTH = 1000  # chars per comment
    MAX_ACTION_ITEMS = 10

    def __init__(self, use_openai: bool = True):
        """
        Initialize the action item generator.

        Args:
            use_openai: Whether to use OpenAI for LLM analysis
        """
        self.use_openai = use_openai and OPENAI_AVAILABLE
        self.openai_client = None

        if self.use_openai:
            try:
                self.openai_client = OpenAI(
                    api_key=os.environ.get("OPENAI_API_KEY"),
                    base_url="https://basecamp.stark.rubrik.com"
                )
            except Exception as e:
                print(f"Warning: Failed to initialize OpenAI client: {e}")
                self.use_openai = False

    def generate_action_items(self, pr_data: Dict[str, Any]) -> ActionItemAnalysis:
        """
        Generate action items from PR comments using LLM analysis.

        Args:
            pr_data: PR data containing comment information

        Returns:
            ActionItemAnalysis with generated action items and analysis
        """
        # Extract and filter comments
        comments_data = self._extract_comments_data(pr_data)

        if not comments_data:
            return self._create_fallback_action_items(pr_data)

        # Filter out bot comments and prepare for analysis
        human_comments = self._filter_human_comments(comments_data)

        if not human_comments:
            return self._create_fallback_action_items(pr_data)

        # Generate action items using LLM or heuristics
        if self.use_openai and self.openai_client:
            return self._llm_generate_action_items(human_comments, pr_data)
        else:
            return self._heuristic_generate_action_items(human_comments, pr_data)

    def _extract_comments_data(self, pr_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract all comments from PR data."""
        all_comments = []

        # Get comments from the structured format
        comments = pr_data.get('comments', {})

        # Add global comments (discussion and review summaries)
        global_comments = comments.get('global_comments', [])
        for comment in global_comments:
            all_comments.append({
                'type': comment.get('type', 'discussion'),
                'author': comment.get('author', 'Unknown'),
                'created_at': comment.get('created_at', ''),
                'body': comment.get('body', ''),
                'context': 'global'
            })

        # Add inline comments (code review comments)
        inline_comments = comments.get('inline_comments', [])
        for comment in inline_comments:
            all_comments.append({
                'type': 'inline',
                'author': comment.get('author', 'Unknown'),
                'created_at': comment.get('created_at', ''),
                'body': comment.get('body', ''),
                'file_path': comment.get('file_path', ''),
                'line_number': comment.get('line_number', ''),
                'context': 'inline'
            })

        return all_comments

    def _filter_human_comments(self, comments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter out bot comments and prepare human comments for analysis."""
        human_comments = []

        for comment in comments:
            author = comment.get('author', '')
            body = comment.get('body', '').strip()

            # Skip bot comments
            if self._is_bot_comment(author):
                continue

            # Skip empty comments
            if not body:
                continue

            # Truncate very long comments
            if len(body) > self.MAX_COMMENT_LENGTH:
                body = body[:self.MAX_COMMENT_LENGTH] + "... [truncated]"
                comment = comment.copy()
                comment['body'] = body

            human_comments.append(comment)

        # Sort by creation time and limit number
        human_comments.sort(key=lambda x: x.get('created_at', ''))
        return human_comments[:self.MAX_COMMENTS_TO_ANALYZE]

    def _is_bot_comment(self, author: str) -> bool:
        """Check if a comment is from a bot account."""
        return any(pattern in author for pattern in self.BOT_PATTERNS)

    def _llm_generate_action_items(self, comments: List[Dict[str, Any]], pr_data: Dict[str, Any]) -> ActionItemAnalysis:
        """Generate action items using OpenAI LLM."""
        try:
            # Create system prompt for action item generation
            system_prompt = self._create_action_item_prompt()

            # Create user prompt with comments
            user_prompt = self._create_comments_prompt(comments, pr_data)

            # Call OpenAI API
            response = self.openai_client.chat.completions.create(
                model="gpt-4.1",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,  # Low temperature for consistent, focused output
                max_tokens=400    # Limit response length
            )

            # Parse the response
            llm_response = response.choices[0].message.content.strip()
            action_items, comment_summary, pending_responses = self._parse_action_item_response(llm_response)

            return ActionItemAnalysis(
                action_items=action_items,
                comment_summary=comment_summary,
                total_comments_analyzed=len(comments),
                pending_responses=pending_responses
            )

        except Exception as e:
            print(f"Warning: OpenAI action item generation failed: {e}")
            # Fall back to heuristic analysis
            return self._heuristic_generate_action_items(comments, pr_data)

    def _create_action_item_prompt(self) -> str:
        """Create system prompt for action item generation."""
        return """You are a code review assistant. Analyze PR comments to generate actionable items for the PR author.

REQUIREMENTS:
1. Generate specific, actionable items based on reviewer comments and feedback
2. Focus on items that require the PR author's attention or response
3. Prioritize technical feedback, requested changes, and unanswered questions
4. Ignore general praise, acknowledgments, or resolved discussions
5. Be concise - each action item should be 1-2 lines maximum
6. Limit to maximum 8 action items to avoid overwhelming the author
7. Include a brief summary of the overall comment sentiment

OUTPUT FORMAT:
ACTION_ITEMS:
- [Specific action item 1]
- [Specific action item 2]
...

COMMENT_SUMMARY: [1-2 line summary of overall feedback tone and focus]
PENDING_RESPONSES: [number of comments that appear to need author response]

EXAMPLES:
ACTION_ITEMS:
- Address memory leak concern in UserService.cleanup() method
- Add unit tests for the new authentication flow as requested
- Clarify the error handling strategy for network timeouts
- Update documentation for the new API endpoint parameters

COMMENT_SUMMARY: Mixed feedback with technical concerns about memory management and requests for additional testing
PENDING_RESPONSES: 3

Be specific, actionable, and focus on what the author needs to do next."""

    def _create_comments_prompt(self, comments: List[Dict[str, Any]], pr_data: Dict[str, Any]) -> str:
        """Create user prompt with comment content."""
        metadata = pr_data.get('metadata', {})
        pr_author = metadata.get('author', 'Unknown')
        pr_title = pr_data.get('pr_title', 'Unknown PR')

        prompt_parts = [
            f"PR: {pr_title}",
            f"Author: {pr_author}",
            f"Total Comments: {len(comments)}",
            "",
            "COMMENTS TO ANALYZE:"
        ]

        for i, comment in enumerate(comments, 1):
            author = comment.get('author', 'Unknown')
            body = comment.get('body', '')
            context = comment.get('context', 'global')

            # Add context information
            context_info = ""
            if context == 'inline':
                file_path = comment.get('file_path', '')
                line_number = comment.get('line_number', '')
                if file_path:
                    context_info = f" (on {file_path}:{line_number})"

            prompt_parts.append(f"Comment {i} by {author}{context_info}:")
            prompt_parts.append(f"{body}")
            prompt_parts.append("")

        return "\n".join(prompt_parts)

    def _parse_action_item_response(self, response: str) -> tuple[List[str], str, int]:
        """Parse LLM response into action items, summary, and pending count."""
        action_items = []
        comment_summary = ""
        pending_responses = 0

        lines = response.strip().split('\n')
        current_section = None

        for line in lines:
            line = line.strip()

            if line.startswith('ACTION_ITEMS:'):
                current_section = 'actions'
                continue
            elif line.startswith('COMMENT_SUMMARY:'):
                current_section = 'summary'
                comment_summary = line[16:].strip()
                continue
            elif line.startswith('PENDING_RESPONSES:'):
                current_section = 'pending'
                pending_text = line[18:].strip()
                try:
                    pending_responses = int(pending_text.split()[0])
                except (ValueError, IndexError):
                    pending_responses = 0
                continue

            # Process content based on current section
            if current_section == 'actions' and line.startswith('- '):
                action_item = line[2:].strip()
                if action_item and len(action_items) < self.MAX_ACTION_ITEMS:
                    action_items.append(action_item)
            elif current_section == 'summary' and line and not comment_summary:
                comment_summary = line

        # Fallback values
        if not comment_summary:
            comment_summary = "Comments analyzed for action items"

        if not action_items:
            action_items = ["Review and address reviewer feedback"]

        return action_items, comment_summary, pending_responses

    def _heuristic_generate_action_items(self, comments: List[Dict[str, Any]], pr_data: Dict[str, Any]) -> ActionItemAnalysis:
        """Generate action items using heuristic analysis."""
        action_items = []
        metadata = pr_data.get('metadata', {})
        pr_author = metadata.get('author', '')

        # Count different types of comments
        questions = 0
        change_requests = 0
        pending_responses = 0

        # Analyze comments for patterns
        for comment in comments:
            author = comment.get('author', '')
            body = comment.get('body', '').lower()

            # Skip author's own comments for pending response calculation
            if author == pr_author:
                continue

            # Count questions
            if '?' in body or 'why' in body or 'how' in body or 'what' in body:
                questions += 1

            # Count change requests
            if any(keyword in body for keyword in ['change', 'fix', 'update', 'modify', 'add', 'remove', 'should']):
                change_requests += 1

            # This is a non-author comment that might need response
            pending_responses += 1

        # Generate action items based on analysis
        if change_requests > 0:
            action_items.append(f"Address {change_requests} requested change(s) from reviewers")

        if questions > 0:
            action_items.append(f"Respond to {questions} question(s) from reviewers")

        # Check PR state for additional actions
        state = metadata.get('state', '')
        if state == 'open':
            reviewers = metadata.get('reviewers', [])
            if reviewers:
                action_items.append("Await reviewer approval")
            elif not comments:
                action_items.append("Request code review")

        # Check for merge conflicts or CI failures mentioned in comments
        for comment in comments:
            body = comment.get('body', '').lower()
            if 'conflict' in body or 'merge conflict' in body:
                action_items.append("Resolve merge conflicts")
                break
            elif 'test' in body and ('fail' in body or 'error' in body):
                action_items.append("Fix failing tests")
                break

        # Fallback if no specific actions found
        if not action_items and comments:
            action_items.append("Review and address feedback from reviewers")
        elif not action_items:
            action_items.append("Request code review")

        # Generate comment summary
        if comments:
            comment_summary = f"Analyzed {len(comments)} comments with {change_requests} change requests and {questions} questions"
        else:
            comment_summary = "No comments to analyze"

        return ActionItemAnalysis(
            action_items=action_items[:self.MAX_ACTION_ITEMS],
            comment_summary=comment_summary,
            total_comments_analyzed=len(comments),
            pending_responses=pending_responses
        )

    def _create_fallback_action_items(self, pr_data: Dict[str, Any]) -> ActionItemAnalysis:
        """Create fallback action items when no comments are available."""
        metadata = pr_data.get('metadata', {})
        state = metadata.get('state', '')

        action_items = []

        if state == 'open':
            reviewers = metadata.get('reviewers', [])
            if reviewers:
                action_items.append("Await reviewer approval")
            else:
                action_items.append("Request code review")
        elif state == 'draft':
            action_items.append("Complete PR and request review")
        else:
            action_items.append("Review PR status")

        return ActionItemAnalysis(
            action_items=action_items,
            comment_summary="No comments available for analysis",
            total_comments_analyzed=0,
            pending_responses=0
        )


def generate_action_items_from_comments(pr_data: Dict[str, Any], generator: ActionItemGenerator = None, use_openai: bool = True) -> List[str]:
    """
    Generate action items from PR comments using LLM analysis.

    Args:
        pr_data: PR data containing comment information
        generator: Optional ActionItemGenerator instance
        use_openai: Whether to use OpenAI for LLM analysis

    Returns:
        List of action items
    """
    if generator is None:
        generator = ActionItemGenerator(use_openai=use_openai)

    # Get action item analysis
    analysis = generator.generate_action_items(pr_data)

    return analysis.action_items


def create_enhanced_summary_with_diff_analysis(pr_data: Dict[str, Any], analyzer: DiffAnalyzer = None, use_openai: bool = True) -> str:
    """
    Create enhanced summary that includes diff analysis.

    Args:
        pr_data: PR data
        analyzer: Optional DiffAnalyzer instance
        use_openai: Whether to use OpenAI for LLM analysis

    Returns:
        Enhanced summary string (max 1000 chars)
    """
    if analyzer is None:
        analyzer = DiffAnalyzer(use_openai=use_openai)

    # Get diff analysis
    diff_analysis = analyzer.analyze_pr_diff(pr_data)

    # Start with diff analysis
    summary_parts = [diff_analysis.overall_summary]

    # Add top file changes (max 3)
    if diff_analysis.file_summaries:
        file_details = []
        for fs in diff_analysis.file_summaries[:3]:
            file_details.append(f"• {fs.filename}: {fs.summary}")

        if file_details:
            summary_parts.append("Key changes:\n" + "\n".join(file_details))

    # Add metadata
    metadata = pr_data.get('metadata', {})
    author = metadata.get('author', 'Unknown')
    state = metadata.get('state', 'unknown')
    reviewers = len(metadata.get('reviewers', []))

    meta_info = f"Author: {author}, State: {state}"
    if reviewers > 0:
        meta_info += f", Reviewers: {reviewers}"

    summary_parts.append(meta_info)

    # Combine with newlines for better formatting
    full_summary = "\n\n".join(summary_parts)
    if len(full_summary) > 1000:
        full_summary = full_summary[:997] + "..."

    return full_summary
