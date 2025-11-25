"""Parse and categorize review comments from Copilot and Perplexity.

This module parses review comments to extract:
- Priority levels (Critical, High, Medium, Low, Deferred)
- Issue descriptions
- File and line references
- Actionable items vs. suggestions
"""

import re
import logging
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple

logger = logging.getLogger(__name__)


class ReviewPriority(Enum):
    """Priority levels for review items."""
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"
    DEFERRED = "Deferred"
    INFO = "Info"  # Informational only, no action needed


@dataclass
class ReviewItem:
    """A single review item from Copilot or Perplexity."""
    priority: ReviewPriority
    description: str
    file: Optional[str] = None
    line: Optional[int] = None
    reviewer: str = "unknown"  # 'copilot', 'perplexity', 'human'
    category: Optional[str] = None  # 'security', 'performance', 'bug', etc.
    suggestion: Optional[str] = None  # Recommended fix
    raw_text: str = ""
    
    def is_blocking(self) -> bool:
        """Check if this item blocks merge."""
        return self.priority in [ReviewPriority.CRITICAL, ReviewPriority.HIGH]
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for storage."""
        return {
            'priority': self.priority.value,
            'description': self.description,
            'file': self.file,
            'line': self.line,
            'reviewer': self.reviewer,
            'category': self.category,
            'suggestion': self.suggestion,
        }


class ReviewParser:
    """Parse review comments from Copilot and Perplexity.
    
    Example:
        >>> parser = ReviewParser()
        >>> comments = monitor.get_pr_comments(522)
        >>> items = parser.parse_all_comments(comments)
        >>> blocking = [i for i in items if i.is_blocking()]
        >>> deferred = [i for i in items if i.priority == ReviewPriority.DEFERRED]
    """
    
    # Keywords for priority detection
    PRIORITY_KEYWORDS = {
        ReviewPriority.CRITICAL: [
            'critical', 'security', 'vulnerability', 'exploit',
            'data loss', 'crash', 'fatal', 'breaking'
        ],
        ReviewPriority.HIGH: [
            'high priority', 'important', 'must fix', 'required',
            'bug', 'error', 'incorrect', 'broken'
        ],
        ReviewPriority.MEDIUM: [
            'medium', 'should fix', 'improvement', 'enhance',
            'refactor', 'cleanup'
        ],
        ReviewPriority.LOW: [
            'low', 'minor', 'nice to have', 'consider',
            'suggestion', 'optional'
        ],
        ReviewPriority.DEFERRED: [
            'defer', 'future', 'later', 'follow-up',
            'separate pr', 'out of scope', 'technical debt'
        ],
    }
    
    # Category keywords
    CATEGORY_KEYWORDS = {
        'security': ['security', 'vulnerability', 'auth', 'xss', 'injection'],
        'performance': ['performance', 'slow', 'optimize', 'efficiency', 'memory'],
        'bug': ['bug', 'error', 'incorrect', 'wrong', 'broken'],
        'style': ['style', 'formatting', 'naming', 'convention'],
        'testing': ['test', 'coverage', 'edge case'],
        'documentation': ['doc', 'comment', 'readme', 'jsdoc'],
    }
    
    def parse_all_comments(self, comments: List[Dict]) -> List[ReviewItem]:
        """Parse all comments and extract review items.
        
        Args:
            comments: List of GitHub comment dicts
            
        Returns:
            List of ReviewItem objects
        """
        items = []
        
        for comment in comments:
            user = comment.get('user', {})
            body = comment.get('body', '')
            login = user.get('login', '')
            
            # Determine reviewer type
            if login == 'github-actions[bot]':
                if '🔍 Perplexity Code Review' in body:
                    reviewer = 'perplexity'
                    comment_items = self.parse_perplexity_comment(body, comment)
                else:
                    reviewer = 'copilot'
                    comment_items = self.parse_copilot_comment(body, comment)
            elif login.endswith('[bot]'):
                reviewer = 'bot'
                comment_items = self.parse_generic_comment(body, comment)
            else:
                reviewer = 'human'
                comment_items = self.parse_generic_comment(body, comment)
            
            # Set reviewer on all items
            for item in comment_items:
                item.reviewer = reviewer
            
            items.extend(comment_items)
        
        logger.info(f"Parsed {len(items)} review items from {len(comments)} comments")
        return items
    
    def parse_perplexity_comment(self, body: str, comment: Dict) -> List[ReviewItem]:
        """Parse Perplexity review comment.
        
        Perplexity format (based on workflow):
        ## 🔍 Perplexity Code Review
        
        ### Key Findings
        - **Security**: [description]
        - **Performance**: [description]
        
        ### Recommendations
        1. [recommendation]
        
        Args:
            body: Comment body text
            comment: Full comment dict
            
        Returns:
            List of ReviewItem objects
        """
        items = []
        
        # Split into sections
        sections = self._split_into_sections(body)
        
        # Parse "Key Findings" section
        if 'key findings' in sections:
            findings = sections['key findings']
            items.extend(self._parse_bullet_list(findings, comment))
        
        # Parse "Recommendations" section
        if 'recommendations' in sections:
            recs = sections['recommendations']
            items.extend(self._parse_numbered_list(recs, comment))
        
        # Parse "Critical Issues" section if present
        if 'critical' in sections:
            critical = sections['critical']
            critical_items = self._parse_bullet_list(critical, comment)
            for item in critical_items:
                item.priority = ReviewPriority.CRITICAL
            items.extend(critical_items)
        
        # If no structured items found, parse as generic
        if not items:
            items = self.parse_generic_comment(body, comment)
        
        return items
    
    def parse_copilot_comment(self, body: str, comment: Dict) -> List[ReviewItem]:
        """Parse Copilot review comment.
        
        Copilot typically provides inline suggestions or summary comments.
        
        Args:
            body: Comment body text
            comment: Full comment dict
            
        Returns:
            List of ReviewItem objects
        """
        items = []
        
        # Check if this is an inline review comment
        if 'path' in comment:
            # Inline comment on specific file/line
            item = self._create_item_from_text(body, comment)
            item.file = comment.get('path')
            item.line = comment.get('line') or comment.get('original_line')
            items.append(item)
        else:
            # Summary comment
            items = self.parse_generic_comment(body, comment)
        
        return items
    
    def parse_generic_comment(self, body: str, comment: Dict) -> List[ReviewItem]:
        """Parse a generic comment using heuristics.
        
        Args:
            body: Comment body text
            comment: Full comment dict
            
        Returns:
            List of ReviewItem objects
        """
        items = []
        
        # Split by lines and look for bullet points or numbered lists
        lines = body.split('\n')
        current_item = []
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            # Check if this is a list item
            if re.match(r'^[-*\d\.]\s+', line):
                # Save previous item
                if current_item:
                    text = ' '.join(current_item)
                    item = self._create_item_from_text(text, comment)
                    items.append(item)
                    current_item = []
                
                # Start new item
                # Remove bullet/number
                text = re.sub(r'^[-*\d\.]\s+', '', line)
                current_item = [text]
            elif current_item:
                # Continuation of current item
                current_item.append(line)
        
        # Save last item
        if current_item:
            text = ' '.join(current_item)
            item = self._create_item_from_text(text, comment)
            items.append(item)
        
        # If no list items found, treat whole comment as one item
        if not items:
            item = self._create_item_from_text(body, comment)
            items.append(item)
        
        return items
    
    def _create_item_from_text(self, text: str, comment: Dict) -> ReviewItem:
        """Create a ReviewItem from text using keyword detection.
        
        Args:
            text: Item text
            comment: Original comment dict
            
        Returns:
            ReviewItem with detected priority and category
        """
        text_lower = text.lower()
        
        # Detect priority
        priority = self._detect_priority(text_lower)
        
        # Detect category
        category = self._detect_category(text_lower)
        
        # Extract file/line if mentioned
        file, line = self._extract_file_reference(text)
        
        # Extract suggestion if present
        suggestion = self._extract_suggestion(text)
        
        return ReviewItem(
            priority=priority,
            description=text,
            file=file,
            line=line,
            category=category,
            suggestion=suggestion,
            raw_text=text
        )
    
    def _detect_priority(self, text: str) -> ReviewPriority:
        """Detect priority from text using keywords.
        
        Args:
            text: Text to analyze (lowercase)
            
        Returns:
            Detected ReviewPriority
        """
        # Check explicit priority markers
        if re.search(r'\[critical\]|\*\*critical\*\*', text, re.I):
            return ReviewPriority.CRITICAL
        if re.search(r'\[high\]|\*\*high\*\*', text, re.I):
            return ReviewPriority.HIGH
        if re.search(r'\[medium\]|\*\*medium\*\*', text, re.I):
            return ReviewPriority.MEDIUM
        if re.search(r'\[low\]|\*\*low\*\*', text, re.I):
            return ReviewPriority.LOW
        if re.search(r'\[deferred\]|\*\*deferred\*\*', text, re.I):
            return ReviewPriority.DEFERRED
        
        # Check keywords
        for priority, keywords in self.PRIORITY_KEYWORDS.items():
            if any(keyword in text for keyword in keywords):
                return priority
        
        # Default to Medium if no keywords match
        return ReviewPriority.MEDIUM
    
    def _detect_category(self, text: str) -> Optional[str]:
        """Detect category from text using keywords.
        
        Args:
            text: Text to analyze (lowercase)
            
        Returns:
            Category string or None
        """
        for category, keywords in self.CATEGORY_KEYWORDS.items():
            if any(keyword in text for keyword in keywords):
                return category
        return None
    
    def _extract_file_reference(self, text: str) -> Tuple[Optional[str], Optional[int]]:
        """Extract file path and line number from text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Tuple of (file_path, line_number)
        """
        # Look for patterns like "src/file.ts:42" or "in file.ts line 42"
        file_pattern = r'(?:in\s+)?([a-zA-Z0-9_/.+-]+\.[a-z]+)(?::(\d+)|[\s,]+line\s+(\d+))?'
        match = re.search(file_pattern, text)
        
        if match:
            file = match.group(1)
            line = match.group(2) or match.group(3)
            return (file, int(line) if line else None)
        
        return (None, None)
    
    def _extract_suggestion(self, text: str) -> Optional[str]:
        """Extract suggested fix from text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Suggestion text or None
        """
        # Look for patterns like "Suggestion: ...", "Consider: ...", "Fix: ..."
        suggestion_pattern = r'(?:suggestion|consider|fix|recommended?|should):\s*(.+?)(?:\.|$)'
        match = re.search(suggestion_pattern, text, re.I)
        
        if match:
            return match.group(1).strip()
        
        return None
    
    def _split_into_sections(self, text: str) -> Dict[str, str]:
        """Split markdown text into sections by headers.
        
        Args:
            text: Markdown text
            
        Returns:
            Dict of section_name -> section_content
        """
        sections = {}
        current_section = None
        current_content = []
        
        for line in text.split('\n'):
            # Check for header
            if line.startswith('#'):
                # Save previous section
                if current_section:
                    sections[current_section.lower()] = '\n'.join(current_content)
                
                # Start new section
                current_section = re.sub(r'^#+\s*', '', line).strip()
                current_content = []
            elif current_section:
                current_content.append(line)
        
        # Save last section
        if current_section:
            sections[current_section.lower()] = '\n'.join(current_content)
        
        return sections
    
    def _parse_bullet_list(self, text: str, comment: Dict) -> List[ReviewItem]:
        """Parse markdown bullet list into items.
        
        Args:
            text: Text containing bullet list
            comment: Original comment dict
            
        Returns:
            List of ReviewItem objects
        """
        items = []
        
        for line in text.split('\n'):
            line = line.strip()
            if re.match(r'^[-*]\s+', line):
                # Remove bullet
                text = re.sub(r'^[-*]\s+', '', line)
                # Check for bold category like "**Security**: description"
                category_match = re.match(r'\*\*([^*]+)\*\*:\s*(.+)', text)
                if category_match:
                    category = category_match.group(1).lower()
                    description = category_match.group(2)
                    item = self._create_item_from_text(description, comment)
                    item.category = category
                    items.append(item)
                else:
                    item = self._create_item_from_text(text, comment)
                    items.append(item)
        
        return items
    
    def _parse_numbered_list(self, text: str, comment: Dict) -> List[ReviewItem]:
        """Parse markdown numbered list into items.
        
        Args:
            text: Text containing numbered list
            comment: Original comment dict
            
        Returns:
            List of ReviewItem objects
        """
        items = []
        
        for line in text.split('\n'):
            line = line.strip()
            if re.match(r'^\d+\.\s+', line):
                # Remove number
                text = re.sub(r'^\d+\.\s+', '', line)
                item = self._create_item_from_text(text, comment)
                items.append(item)
        
        return items
    
    def categorize_items(self, items: List[ReviewItem]) -> Dict[str, List[ReviewItem]]:
        """Categorize items by priority.
        
        Args:
            items: List of ReviewItem objects
            
        Returns:
            Dict of priority_name -> items
        """
        categorized = {
            'critical': [],
            'high': [],
            'medium': [],
            'low': [],
            'deferred': [],
            'info': [],
        }
        
        for item in items:
            key = item.priority.value.lower()
            if key in categorized:
                categorized[key].append(item)
        
        return categorized
    
    def get_blocking_items(self, items: List[ReviewItem]) -> List[ReviewItem]:
        """Get items that block merge.
        
        Args:
            items: List of ReviewItem objects
            
        Returns:
            List of blocking items
        """
        return [item for item in items if item.is_blocking()]
    
    def get_deferred_items(self, items: List[ReviewItem]) -> List[ReviewItem]:
        """Get items marked as deferred.
        
        Args:
            items: List of ReviewItem objects
            
        Returns:
            List of deferred items
        """
        return [item for item in items if item.priority == ReviewPriority.DEFERRED]


# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Example comment
    example_comment = {
        'user': {'login': 'github-actions[bot]'},
        'body': '''## 🔍 Perplexity Code Review

### Key Findings
- **Security**: Potential XSS vulnerability in user input handling
- **Performance**: Consider memoizing the expensive calculation in line 42
- **Bug**: Edge case not handled when array is empty

### Recommendations
1. Add input sanitization before rendering
2. Implement caching for frequently called functions
3. Add null checks for empty arrays

### Deferred Items
- Consider migrating to TypeScript 5.0 (separate PR)
- Refactor legacy code in utils.js (technical debt)
'''
    }
    
    parser = ReviewParser()
    items = parser.parse_perplexity_comment(example_comment['body'], example_comment)
    
    print(f"\n{'='*60}")
    print(f"Parsed {len(items)} review items")
    print(f"{'='*60}\n")
    
    for item in items:
        print(f"Priority: {item.priority.value}")
        print(f"Category: {item.category}")
        print(f"Description: {item.description}")
        print(f"Blocking: {item.is_blocking()}")
        print("-" * 60)
    
    # Categorize
    categorized = parser.categorize_items(items)
    print(f"\nCategorized:")
    for priority, items_list in categorized.items():
        if items_list:
            print(f"  {priority.title()}: {len(items_list)} items")
    
    # Get deferred
    deferred = parser.get_deferred_items(items)
    print(f"\nDeferred items: {len(deferred)}")
    for item in deferred:
        print(f"  - {item.description}")
