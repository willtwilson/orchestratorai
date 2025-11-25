"""Remediation plan management and deferred issue creation.

This module:
- Creates actionable remediation plans from review items
- Auto-creates GitHub issues for deferred tasks
- Tracks completion of remediation items
"""

import os
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional
import requests

from ..monitoring.review_parser import ReviewItem, ReviewPriority

logger = logging.getLogger(__name__)


@dataclass
class RemediationPlan:
    """Plan for addressing review items."""
    pr_number: int
    created_at: datetime
    critical_items: List[ReviewItem] = field(default_factory=list)
    high_items: List[ReviewItem] = field(default_factory=list)
    medium_items: List[ReviewItem] = field(default_factory=list)
    low_items: List[ReviewItem] = field(default_factory=list)
    deferred_items: List[ReviewItem] = field(default_factory=list)
    deferred_issue_number: Optional[int] = None
    
    def has_blocking_items(self) -> bool:
        """Check if plan has blocking items."""
        return len(self.critical_items) > 0 or len(self.high_items) > 0
    
    def total_items(self) -> int:
        """Get total number of items."""
        return (
            len(self.critical_items) +
            len(self.high_items) +
            len(self.medium_items) +
            len(self.low_items) +
            len(self.deferred_items)
        )
    
    def actionable_items(self) -> List[ReviewItem]:
        """Get all actionable (non-deferred) items."""
        return (
            self.critical_items +
            self.high_items +
            self.medium_items +
            self.low_items
        )
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for storage."""
        return {
            'pr_number': self.pr_number,
            'created_at': self.created_at.isoformat(),
            'critical_items': [item.to_dict() for item in self.critical_items],
            'high_items': [item.to_dict() for item in self.high_items],
            'medium_items': [item.to_dict() for item in self.medium_items],
            'low_items': [item.to_dict() for item in self.low_items],
            'deferred_items': [item.to_dict() for item in self.deferred_items],
            'deferred_issue_number': self.deferred_issue_number,
            'has_blocking_items': self.has_blocking_items(),
            'total_items': self.total_items(),
        }


class PlanManager:
    """Manage remediation plans and deferred issues.
    
    Example:
        >>> manager = PlanManager(github_token="...", repo="owner/repo")
        >>> plan = manager.create_plan(pr_number=522, review_items=items)
        >>> if plan.deferred_items:
        ...     issue_num = manager.create_deferred_issue(plan, pr_number=522)
        ...     print(f"Created deferred issue #{issue_num}")
    """
    
    def __init__(self, github_token: str, repo: str):
        """Initialize plan manager.
        
        Args:
            github_token: GitHub API token
            repo: Repository in format "owner/name"
        """
        self.github_token = github_token
        self.repo = repo
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {github_token}",
            "Accept": "application/vnd.github.v3+json"
        }
    
    def create_plan(self, pr_number: int, review_items: List[ReviewItem]) -> RemediationPlan:
        """Create remediation plan from review items.
        
        Args:
            pr_number: Pull request number
            review_items: List of ReviewItem objects
            
        Returns:
            RemediationPlan with categorized items
        """
        logger.info(f"Creating remediation plan for PR #{pr_number} with {len(review_items)} items")
        
        plan = RemediationPlan(
            pr_number=pr_number,
            created_at=datetime.now()
        )
        
        # Categorize items by priority
        for item in review_items:
            if item.priority == ReviewPriority.CRITICAL:
                plan.critical_items.append(item)
            elif item.priority == ReviewPriority.HIGH:
                plan.high_items.append(item)
            elif item.priority == ReviewPriority.MEDIUM:
                plan.medium_items.append(item)
            elif item.priority == ReviewPriority.LOW:
                plan.low_items.append(item)
            elif item.priority == ReviewPriority.DEFERRED:
                plan.deferred_items.append(item)
        
        logger.info(
            f"Plan created: {len(plan.critical_items)} critical, "
            f"{len(plan.high_items)} high, {len(plan.medium_items)} medium, "
            f"{len(plan.low_items)} low, {len(plan.deferred_items)} deferred"
        )
        
        return plan
    
    def create_deferred_issue(
        self, 
        plan: RemediationPlan, 
        pr_number: int,
        original_issue_number: Optional[int] = None
    ) -> Optional[int]:
        """Create GitHub issue for deferred items.
        
        Args:
            plan: RemediationPlan with deferred items
            pr_number: Pull request number
            original_issue_number: Original issue number if available
            
        Returns:
            Created issue number or None if failed
        """
        if not plan.deferred_items:
            logger.info("No deferred items to create issue for")
            return None
        
        logger.info(f"Creating deferred issue for {len(plan.deferred_items)} items from PR #{pr_number}")
        
        # Build issue body
        title = f"Deferred Tasks from PR #{pr_number}"
        body = self._build_deferred_issue_body(plan, pr_number, original_issue_number)
        labels = ["deferred", "technical-debt", "orchestratorai"]
        
        try:
            # Create issue via GitHub API
            url = f"{self.base_url}/repos/{self.repo}/issues"
            data = {
                "title": title,
                "body": body,
                "labels": labels
            }
            
            response = requests.post(url, headers=self.headers, json=data, timeout=10)
            response.raise_for_status()
            
            issue = response.json()
            issue_number = issue['number']
            
            logger.info(f"✓ Created deferred issue #{issue_number}")
            plan.deferred_issue_number = issue_number
            
            # Add comment to original PR linking to deferred issue
            self._link_deferred_issue_to_pr(pr_number, issue_number)
            
            return issue_number
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to create deferred issue: {e}")
            return None
    
    def _build_deferred_issue_body(
        self,
        plan: RemediationPlan,
        pr_number: int,
        original_issue_number: Optional[int]
    ) -> str:
        """Build markdown body for deferred issue.
        
        Args:
            plan: RemediationPlan with deferred items
            pr_number: Pull request number
            original_issue_number: Original issue number if available
            
        Returns:
            Markdown formatted issue body
        """
        lines = [
            f"# Deferred Tasks from PR #{pr_number}",
            "",
            "These items were identified during code review but deferred for future work:",
            ""
        ]
        
        # Group by category if available
        categorized = {}
        uncategorized = []
        
        for item in plan.deferred_items:
            if item.category:
                if item.category not in categorized:
                    categorized[item.category] = []
                categorized[item.category].append(item)
            else:
                uncategorized.append(item)
        
        # Add categorized items
        for category, items in categorized.items():
            lines.append(f"## {category.title()}")
            lines.append("")
            for item in items:
                checkbox = "- [ ]"
                description = item.description
                if item.file:
                    description += f" (in `{item.file}`"
                    if item.line:
                        description += f" line {item.line}"
                    description += ")"
                lines.append(f"{checkbox} {description}")
            lines.append("")
        
        # Add uncategorized items
        if uncategorized:
            lines.append("## Other Tasks")
            lines.append("")
            for item in uncategorized:
                checkbox = "- [ ]"
                description = item.description
                if item.file:
                    description += f" (in `{item.file}`"
                    if item.line:
                        description += f" line {item.line}"
                    description += ")"
                lines.append(f"{checkbox} {description}")
            lines.append("")
        
        # Add context
        lines.extend([
            "---",
            "",
            "**Context:**",
            f"- Original PR: #{pr_number}",
        ])
        
        if original_issue_number:
            lines.append(f"- Original Issue: #{original_issue_number}")
        
        lines.extend([
            f"- Created: {plan.created_at.strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "**Labels:** `deferred`, `technical-debt`, `orchestratorai`",
            "",
            "---",
            "",
            "🤖 *This issue was automatically created by OrchestratorAI*"
        ])
        
        return "\n".join(lines)
    
    def _link_deferred_issue_to_pr(self, pr_number: int, issue_number: int):
        """Add comment to PR linking to deferred issue.
        
        Args:
            pr_number: Pull request number
            issue_number: Deferred issue number
        """
        try:
            url = f"{self.base_url}/repos/{self.repo}/issues/{pr_number}/comments"
            data = {
                "body": (
                    f"📋 Deferred tasks have been logged in issue #{issue_number}\n\n"
                    f"These items will be addressed in a future PR."
                )
            }
            
            response = requests.post(url, headers=self.headers, json=data, timeout=10)
            response.raise_for_status()
            
            logger.info(f"✓ Linked deferred issue #{issue_number} to PR #{pr_number}")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to link deferred issue to PR: {e}")
    
    def get_plan_summary(self, plan: RemediationPlan) -> str:
        """Get human-readable summary of plan.
        
        Args:
            plan: RemediationPlan
            
        Returns:
            Summary string
        """
        lines = [
            f"Remediation Plan for PR #{plan.pr_number}",
            "=" * 60,
            f"Total Items: {plan.total_items()}",
            ""
        ]
        
        if plan.critical_items:
            lines.append(f"🔴 Critical: {len(plan.critical_items)}")
            for item in plan.critical_items:
                lines.append(f"  - {item.description[:80]}...")
            lines.append("")
        
        if plan.high_items:
            lines.append(f"🟠 High Priority: {len(plan.high_items)}")
            for item in plan.high_items:
                lines.append(f"  - {item.description[:80]}...")
            lines.append("")
        
        if plan.medium_items:
            lines.append(f"🟡 Medium Priority: {len(plan.medium_items)}")
            lines.append("")
        
        if plan.low_items:
            lines.append(f"🟢 Low Priority: {len(plan.low_items)}")
            lines.append("")
        
        if plan.deferred_items:
            lines.append(f"⏭️  Deferred: {len(plan.deferred_items)}")
            if plan.deferred_issue_number:
                lines.append(f"   (Logged in issue #{plan.deferred_issue_number})")
            lines.append("")
        
        if plan.has_blocking_items():
            lines.append("⚠️  **BLOCKING ITEMS PRESENT** - Address before merge")
        else:
            lines.append("✓ No blocking items")
        
        return "\n".join(lines)


# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Example: Create plan from review items
    from ..monitoring.review_parser import ReviewItem, ReviewPriority
    
    items = [
        ReviewItem(
            priority=ReviewPriority.CRITICAL,
            description="Fix XSS vulnerability in user input",
            file="src/utils/input.ts",
            line=42,
            category="security"
        ),
        ReviewItem(
            priority=ReviewPriority.HIGH,
            description="Add null check for empty array",
            file="src/utils/array.ts",
            line=15
        ),
        ReviewItem(
            priority=ReviewPriority.DEFERRED,
            description="Migrate to TypeScript 5.0",
            category="technical-debt"
        ),
        ReviewItem(
            priority=ReviewPriority.DEFERRED,
            description="Refactor legacy utils.js",
            category="technical-debt"
        ),
    ]
    
    manager = PlanManager(
        github_token=os.getenv("GITHUB_TOKEN", ""),
        repo=os.getenv("GITHUB_REPO", "owner/repo")
    )
    
    plan = manager.create_plan(pr_number=522, review_items=items)
    
    print("\n" + manager.get_plan_summary(plan))
    
    # Create deferred issue if needed
    if plan.deferred_items:
        issue_num = manager.create_deferred_issue(plan, pr_number=522, original_issue_number=521)
        if issue_num:
            print(f"\n✓ Deferred issue created: #{issue_num}")
