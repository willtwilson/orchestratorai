"""Merge recommendation system.

This module determines if a PR is ready to merge based on:
- Review completion (Copilot, Perplexity, humans)
- Blocking issues resolution
- CI checks status
- Approval status
"""

import logging
from dataclasses import dataclass
from typing import List, Optional
from enum import Enum

from .plan_manager import RemediationPlan
from ..monitoring.pr_monitor import PRMonitor, ReviewStatus

logger = logging.getLogger(__name__)


class MergeReadiness(Enum):
    """Merge readiness states."""
    READY = "ready"
    BLOCKED = "blocked"
    WAITING_REVIEWS = "waiting_reviews"
    WAITING_CI = "waiting_ci"
    WAITING_APPROVAL = "waiting_approval"
    DRAFT = "draft"


@dataclass
class MergeDecision:
    """Decision on whether PR is ready to merge."""
    pr_number: int
    ready_to_merge: bool
    readiness: MergeReadiness
    reason: str
    blocking_items: List[str]
    recommendations: List[str]
    autopilot_recommended: bool = False
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            'pr_number': self.pr_number,
            'ready_to_merge': self.ready_to_merge,
            'readiness': self.readiness.value,
            'reason': self.reason,
            'blocking_items': self.blocking_items,
            'recommendations': self.recommendations,
            'autopilot_recommended': self.autopilot_recommended,
        }


class MergeRecommender:
    """Recommend merge decisions based on PR status and reviews.
    
    Example:
        >>> recommender = MergeRecommender(
        ...     monitor=pr_monitor,
        ...     require_human_approval=True,
        ...     autopilot_mode=False
        ... )
        >>> decision = recommender.evaluate(
        ...     pr_number=522,
        ...     review_status=status,
        ...     remediation_plan=plan
        ... )
        >>> if decision.ready_to_merge:
        ...     print(f"✓ Ready to merge: {decision.reason}")
        ... else:
        ...     print(f"✗ Not ready: {decision.reason}")
    """
    
    def __init__(
        self,
        monitor: PRMonitor,
        require_human_approval: bool = True,
        require_ci_pass: bool = True,
        autopilot_mode: bool = False
    ):
        """Initialize merge recommender.
        
        Args:
            monitor: PRMonitor instance
            require_human_approval: Require at least one human approval
            require_ci_pass: Require CI checks to pass
            autopilot_mode: Enable autopilot (auto-merge when ready)
        """
        self.monitor = monitor
        self.require_human_approval = require_human_approval
        self.require_ci_pass = require_ci_pass
        self.autopilot_mode = autopilot_mode
    
    def evaluate(
        self,
        pr_number: int,
        review_status: ReviewStatus,
        remediation_plan: RemediationPlan
    ) -> MergeDecision:
        """Evaluate if PR is ready to merge.
        
        Args:
            pr_number: Pull request number
            review_status: ReviewStatus from PRMonitor
            remediation_plan: RemediationPlan from PlanManager
            
        Returns:
            MergeDecision with recommendation
        """
        logger.info(f"Evaluating merge readiness for PR #{pr_number}")
        
        blocking_items = []
        recommendations = []
        
        # Get PR status
        pr_status = self.monitor.get_pr_status(pr_number)
        
        # Check if PR is draft
        if pr_status.get('draft'):
            return MergeDecision(
                pr_number=pr_number,
                ready_to_merge=False,
                readiness=MergeReadiness.DRAFT,
                reason="PR is still in draft mode",
                blocking_items=["PR marked as draft"],
                recommendations=["Mark PR as ready for review"]
            )
        
        # Check if reviews are complete
        if not review_status.all_reviews_complete:
            reason_parts = []
            if not review_status.copilot_complete:
                blocking_items.append("Copilot review not complete")
                reason_parts.append("Copilot review pending")
            if not review_status.perplexity_complete and not review_status.perplexity_failed:
                blocking_items.append("Perplexity review not complete")
                reason_parts.append("Perplexity review pending")
            
            return MergeDecision(
                pr_number=pr_number,
                ready_to_merge=False,
                readiness=MergeReadiness.WAITING_REVIEWS,
                reason=", ".join(reason_parts),
                blocking_items=blocking_items,
                recommendations=["Wait for automated reviews to complete"]
            )
        
        # Check for blocking review items (CRITICAL/HIGH)
        if remediation_plan.has_blocking_items():
            blocking_count = (
                len(remediation_plan.critical_items) +
                len(remediation_plan.high_items)
            )
            
            for item in remediation_plan.critical_items:
                blocking_items.append(f"CRITICAL: {item.description[:60]}")
            
            for item in remediation_plan.high_items:
                blocking_items.append(f"HIGH: {item.description[:60]}")
            
            recommendations.append("Address all critical and high priority items")
            recommendations.append("Push fixes and wait for re-review")
            
            return MergeDecision(
                pr_number=pr_number,
                ready_to_merge=False,
                readiness=MergeReadiness.BLOCKED,
                reason=f"{blocking_count} blocking issues found in review",
                blocking_items=blocking_items,
                recommendations=recommendations
            )
        
        # Check CI status
        if self.require_ci_pass:
            if not pr_status.get('checks_passed'):
                blocking_items.append("CI checks not passing")
                recommendations.append("Fix failing CI checks")
                
                return MergeDecision(
                    pr_number=pr_number,
                    ready_to_merge=False,
                    readiness=MergeReadiness.WAITING_CI,
                    reason="CI checks are failing",
                    blocking_items=blocking_items,
                    recommendations=recommendations
                )
        
        # Check human approval
        if self.require_human_approval:
            if not pr_status.get('approved'):
                blocking_items.append("No human approval")
                recommendations.append("Request review from team member")
                
                return MergeDecision(
                    pr_number=pr_number,
                    ready_to_merge=False,
                    readiness=MergeReadiness.WAITING_APPROVAL,
                    reason="Waiting for human approval",
                    blocking_items=blocking_items,
                    recommendations=recommendations
                )
        
        # Check mergeable state
        if not pr_status.get('mergeable'):
            blocking_items.append("PR has merge conflicts")
            recommendations.append("Resolve merge conflicts")
            
            return MergeDecision(
                pr_number=pr_number,
                ready_to_merge=False,
                readiness=MergeReadiness.BLOCKED,
                reason="PR has merge conflicts",
                blocking_items=blocking_items,
                recommendations=recommendations
            )
        
        # All checks passed!
        recommendations.append("All checks passed - ready to merge")
        
        # Add info about deferred items if any
        if remediation_plan.deferred_items:
            deferred_count = len(remediation_plan.deferred_items)
            recommendations.append(
                f"{deferred_count} deferred items logged for future work"
            )
        
        # Add info about low priority items
        low_count = len(remediation_plan.low_items) + len(remediation_plan.medium_items)
        if low_count > 0:
            recommendations.append(
                f"{low_count} low/medium priority items can be addressed later"
            )
        
        # Determine if autopilot should proceed
        autopilot_recommended = self.autopilot_mode and self._is_safe_for_autopilot(
            pr_status, review_status, remediation_plan
        )
        
        if autopilot_recommended:
            recommendations.append("🤖 Autopilot: Will auto-merge and proceed to next task")
        
        return MergeDecision(
            pr_number=pr_number,
            ready_to_merge=True,
            readiness=MergeReadiness.READY,
            reason="All requirements met",
            blocking_items=[],
            recommendations=recommendations,
            autopilot_recommended=autopilot_recommended
        )
    
    def _is_safe_for_autopilot(
        self,
        pr_status: dict,
        review_status: ReviewStatus,
        remediation_plan: RemediationPlan
    ) -> bool:
        """Determine if it's safe to auto-merge via autopilot.
        
        Args:
            pr_status: PR status dict
            review_status: ReviewStatus
            remediation_plan: RemediationPlan
            
        Returns:
            True if safe for autopilot
        """
        # Additional safety checks for autopilot
        checks = [
            # Must have both reviews complete (no failures/timeouts)
            review_status.copilot_complete and review_status.perplexity_complete,
            
            # No blocking items
            not remediation_plan.has_blocking_items(),
            
            # CI must pass
            pr_status.get('checks_passed', False),
            
            # Must be approved
            pr_status.get('approved', False),
            
            # Must be mergeable
            pr_status.get('mergeable', False),
        ]
        
        is_safe = all(checks)
        
        if is_safe:
            logger.info(f"Autopilot safety checks passed for PR #{pr_status.get('number')}")
        else:
            logger.warning(f"Autopilot safety checks failed for PR #{pr_status.get('number')}")
        
        return is_safe
    
    def format_decision(self, decision: MergeDecision) -> str:
        """Format decision as human-readable string.
        
        Args:
            decision: MergeDecision
            
        Returns:
            Formatted string
        """
        lines = [
            f"{'='*60}",
            f"Merge Recommendation: PR #{decision.pr_number}",
            f"{'='*60}",
            ""
        ]
        
        # Status
        if decision.ready_to_merge:
            lines.append("✅ **READY TO MERGE**")
        else:
            lines.append(f"❌ **NOT READY** ({decision.readiness.value.upper()})")
        
        lines.append(f"Reason: {decision.reason}")
        lines.append("")
        
        # Blocking items
        if decision.blocking_items:
            lines.append("🚫 Blocking Items:")
            for item in decision.blocking_items:
                lines.append(f"  • {item}")
            lines.append("")
        
        # Recommendations
        if decision.recommendations:
            lines.append("💡 Recommendations:")
            for rec in decision.recommendations:
                lines.append(f"  • {rec}")
            lines.append("")
        
        # Autopilot
        if decision.autopilot_recommended:
            lines.append("🤖 **AUTOPILOT ENABLED**")
            lines.append("   Will auto-merge and proceed to next task")
        
        lines.append(f"{'='*60}")
        
        return "\n".join(lines)


# Example usage
if __name__ == "__main__":
    import os
    from .plan_manager import PlanManager, RemediationPlan
    from ..monitoring.pr_monitor import PRMonitor, ReviewStatus
    from ..monitoring.review_parser import ReviewItem, ReviewPriority
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Setup
    monitor = PRMonitor(
        github_token=os.getenv("GITHUB_TOKEN", ""),
        repo=os.getenv("GITHUB_REPO", "owner/repo")
    )
    
    recommender = MergeRecommender(
        monitor=monitor,
        require_human_approval=True,
        require_ci_pass=True,
        autopilot_mode=False
    )
    
    # Example: Evaluate PR that's ready
    review_status = ReviewStatus(
        pr_number=522,
        copilot_complete=True,
        perplexity_complete=True,
        all_reviews_complete=True
    )
    
    plan = RemediationPlan(
        pr_number=522,
        created_at=datetime.now()
    )
    # No blocking items - ready to merge
    
    decision = recommender.evaluate(
        pr_number=522,
        review_status=review_status,
        remediation_plan=plan
    )
    
    print("\n" + recommender.format_decision(decision))
