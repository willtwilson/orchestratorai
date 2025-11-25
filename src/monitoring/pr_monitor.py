"""PR monitoring and review status tracking.

This module monitors GitHub Pull Requests for review completion,
handling both Copilot and Perplexity reviews with graceful error handling
for workflow failures and timeouts.
"""

import os
import time
import logging
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Tuple
import requests

logger = logging.getLogger(__name__)


class ReviewerType(Enum):
    """Types of reviewers."""
    COPILOT = "github-copilot"
    PERPLEXITY = "perplexity"
    HUMAN = "human"


@dataclass
class ReviewStatus:
    """Status of PR reviews."""
    pr_number: int
    copilot_complete: bool = False
    copilot_timestamp: Optional[datetime] = None
    perplexity_complete: bool = False
    perplexity_timestamp: Optional[datetime] = None
    perplexity_failed: bool = False
    perplexity_timeout: bool = False
    all_reviews_complete: bool = False
    error: Optional[str] = None
    workflow_run_id: Optional[int] = None
    workflow_status: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for state storage."""
        return {
            'pr_number': self.pr_number,
            'copilot_complete': self.copilot_complete,
            'copilot_timestamp': self.copilot_timestamp.isoformat() if self.copilot_timestamp else None,
            'perplexity_complete': self.perplexity_complete,
            'perplexity_timestamp': self.perplexity_timestamp.isoformat() if self.perplexity_timestamp else None,
            'perplexity_failed': self.perplexity_failed,
            'perplexity_timeout': self.perplexity_timeout,
            'all_reviews_complete': self.all_reviews_complete,
            'error': self.error,
            'workflow_run_id': self.workflow_run_id,
            'workflow_status': self.workflow_status,
        }


class PRMonitor:
    """Monitor PR status and wait for reviews.
    
    This class handles:
    - Waiting for Copilot reviews
    - Waiting for Perplexity reviews (with timeout/failure fallback)
    - Checking GitHub Actions workflow status
    - Graceful error handling for missing reviews
    
    Example:
        >>> monitor = PRMonitor(github_token="ghp_...", repo="owner/repo")
        >>> status = await monitor.wait_for_reviews(pr_number=522, timeout_minutes=10)
        >>> if status.all_reviews_complete:
        ...     print("Reviews complete!")
        ... elif status.perplexity_failed:
        ...     print("Perplexity failed, but continuing...")
    """
    
    def __init__(
        self,
        github_token: str,
        repo: str,
        perplexity_timeout_minutes: int = 10,
        poll_interval_seconds: int = 30
    ):
        """Initialize PR monitor.
        
        Args:
            github_token: GitHub API token
            repo: Repository in format "owner/name"
            perplexity_timeout_minutes: Max time to wait for Perplexity review
            poll_interval_seconds: How often to check for reviews
        """
        self.github_token = github_token
        self.repo = repo
        self.perplexity_timeout = timedelta(minutes=perplexity_timeout_minutes)
        self.poll_interval = poll_interval_seconds
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {github_token}",
            "Accept": "application/vnd.github.v3+json"
        }
    
    def wait_for_reviews(
        self, 
        pr_number: int,
        timeout_minutes: Optional[int] = None
    ) -> ReviewStatus:
        """Wait for Copilot and Perplexity reviews to complete.
        
        This method:
        1. Waits for Copilot review comment
        2. Waits for Perplexity review comment (with timeout)
        3. If Perplexity times out or fails, logs warning and continues
        4. Returns comprehensive status
        
        Args:
            pr_number: Pull request number
            timeout_minutes: Override default timeout (optional)
            
        Returns:
            ReviewStatus with completion flags and any errors
            
        Example:
            >>> status = monitor.wait_for_reviews(522)
            >>> if status.perplexity_timeout:
            ...     logger.warning("Perplexity timed out, proceeding anyway")
        """
        logger.info(f"Monitoring PR #{pr_number} for reviews...")
        
        timeout = timedelta(minutes=timeout_minutes) if timeout_minutes else self.perplexity_timeout
        start_time = datetime.now()
        status = ReviewStatus(pr_number=pr_number)
        
        # Check if PR exists
        pr = self._get_pr(pr_number)
        if not pr:
            status.error = "PR not found"
            return status
        
        logger.info(f"PR #{pr_number} found: {pr['title']}")
        
        # Main monitoring loop
        while datetime.now() - start_time < timeout:
            # Check Copilot review
            if not status.copilot_complete:
                copilot_found = self._check_copilot_review(pr_number)
                if copilot_found:
                    status.copilot_complete = True
                    status.copilot_timestamp = datetime.now()
                    logger.info(f"✓ Copilot review found for PR #{pr_number}")
            
            # Check Perplexity review
            if not status.perplexity_complete:
                perplexity_found, workflow_failed = self._check_perplexity_review(pr_number)
                if perplexity_found:
                    status.perplexity_complete = True
                    status.perplexity_timestamp = datetime.now()
                    logger.info(f"✓ Perplexity review found for PR #{pr_number}")
                elif workflow_failed:
                    status.perplexity_failed = True
                    logger.warning(
                        f"⚠️ Perplexity workflow failed for PR #{pr_number}. "
                        f"This may be due to rate limits or API errors. Continuing without Perplexity review."
                    )
                    break
            
            # Check if both complete
            if status.copilot_complete and status.perplexity_complete:
                status.all_reviews_complete = True
                logger.info(f"✓ All reviews complete for PR #{pr_number}")
                return status
            
            # Check if Copilot done and Perplexity failed
            if status.copilot_complete and status.perplexity_failed:
                status.all_reviews_complete = True  # Consider complete with warning
                logger.info(f"✓ Copilot review complete, Perplexity failed (continuing)")
                return status
            
            # Wait before next check
            elapsed = datetime.now() - start_time
            remaining = timeout - elapsed
            logger.debug(
                f"Waiting for reviews... "
                f"Copilot: {status.copilot_complete}, "
                f"Perplexity: {status.perplexity_complete}, "
                f"Time remaining: {remaining.total_seconds():.0f}s"
            )
            time.sleep(self.poll_interval)
        
        # Timeout reached
        if not status.copilot_complete:
            logger.warning(f"⚠️ Timeout: Copilot review not found for PR #{pr_number}")
        
        if not status.perplexity_complete and not status.perplexity_failed:
            status.perplexity_timeout = True
            logger.warning(
                f"⚠️ Timeout: Perplexity review not found for PR #{pr_number} "
                f"after {timeout.total_seconds()/60:.1f} minutes. "
                f"Proceeding without Perplexity review."
            )
        
        # If Copilot is complete, consider it acceptable to proceed
        if status.copilot_complete:
            status.all_reviews_complete = True
            logger.info(f"Proceeding with Copilot review only for PR #{pr_number}")
        
        return status
    
    def _get_pr(self, pr_number: int) -> Optional[Dict]:
        """Get PR details from GitHub API.
        
        Args:
            pr_number: Pull request number
            
        Returns:
            PR dict or None if not found
        """
        try:
            url = f"{self.base_url}/repos/{self.repo}/pulls/{pr_number}"
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch PR #{pr_number}: {e}")
            return None
    
    def _check_copilot_review(self, pr_number: int) -> bool:
        """Check if Copilot has posted a review comment.
        
        Copilot posts reviews as comments from 'github-actions[bot]' user
        with specific formatting (usually contains "Copilot" in the body).
        
        Args:
            pr_number: Pull request number
            
        Returns:
            True if Copilot review found
        """
        try:
            # Get PR comments
            url = f"{self.base_url}/repos/{self.repo}/issues/{pr_number}/comments"
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            comments = response.json()
            
            # Look for Copilot review
            for comment in comments:
                user = comment.get('user', {})
                body = comment.get('body', '')
                
                # Check if from github-actions bot and mentions Copilot
                if (user.get('login') == 'github-actions[bot]' and
                    ('copilot' in body.lower() or 'code review' in body.lower())):
                    logger.debug(f"Found Copilot review in comment #{comment['id']}")
                    return True
            
            # Also check review comments (on code lines)
            url = f"{self.base_url}/repos/{self.repo}/pulls/{pr_number}/reviews"
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            reviews = response.json()
            
            for review in reviews:
                user = review.get('user', {})
                if user.get('login') == 'github-actions[bot]':
                    logger.debug(f"Found Copilot review #{review['id']}")
                    return True
            
            return False
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error checking Copilot review for PR #{pr_number}: {e}")
            return False
    
    def _check_perplexity_review(self, pr_number: int) -> Tuple[bool, bool]:
        """Check if Perplexity review comment exists.
        
        Based on the workflow, Perplexity posts as 'github-actions[bot]'
        with a comment starting with '## 🔍 Perplexity Code Review'.
        
        Args:
            pr_number: Pull request number
            
        Returns:
            Tuple of (review_found, workflow_failed)
        """
        try:
            # Get PR comments
            url = f"{self.base_url}/repos/{self.repo}/issues/{pr_number}/comments"
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            comments = response.json()
            
            # Look for Perplexity review marker
            for comment in comments:
                user = comment.get('user', {})
                body = comment.get('body', '')
                
                if (user.get('login') == 'github-actions[bot]' and
                    '🔍 Perplexity Code Review' in body):
                    logger.debug(f"Found Perplexity review in comment #{comment['id']}")
                    return (True, False)
            
            # Check if workflow failed
            workflow_failed = self._check_workflow_status(pr_number)
            if workflow_failed:
                return (False, True)
            
            return (False, False)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error checking Perplexity review for PR #{pr_number}: {e}")
            # On API error, assume workflow might have failed
            return (False, True)
    
    def _check_workflow_status(self, pr_number: int) -> bool:
        """Check if Perplexity workflow has failed.
        
        Args:
            pr_number: Pull request number
            
        Returns:
            True if workflow failed or errored
        """
        try:
            # Get workflow runs for this PR
            url = f"{self.base_url}/repos/{self.repo}/actions/runs"
            params = {
                'event': 'pull_request',
                'per_page': 10
            }
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()
            runs = response.json().get('workflow_runs', [])
            
            # Look for Perplexity workflow run
            for run in runs:
                # Check if this run is for our PR
                if run.get('name') == 'Perplexity Code Review':
                    # Get associated PR from head_branch or pull_requests
                    pull_requests = run.get('pull_requests', [])
                    if any(pr.get('number') == pr_number for pr in pull_requests):
                        status = run.get('status')
                        conclusion = run.get('conclusion')
                        
                        logger.debug(
                            f"Perplexity workflow for PR #{pr_number}: "
                            f"status={status}, conclusion={conclusion}"
                        )
                        
                        # Check if failed
                        if conclusion in ['failure', 'cancelled', 'timed_out']:
                            logger.warning(
                                f"Perplexity workflow failed for PR #{pr_number}: {conclusion}"
                            )
                            return True
                        
                        # If still in progress, not failed yet
                        if status == 'in_progress' or status == 'queued':
                            return False
            
            # No workflow found or still in progress
            return False
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error checking workflow status for PR #{pr_number}: {e}")
            # On API error, assume it might have failed
            return True
    
    def get_pr_reviews(self, pr_number: int) -> List[Dict]:
        """Get all reviews for a PR.
        
        Args:
            pr_number: Pull request number
            
        Returns:
            List of review dicts with user, body, state, submitted_at
        """
        try:
            url = f"{self.base_url}/repos/{self.repo}/pulls/{pr_number}/reviews"
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching reviews for PR #{pr_number}: {e}")
            return []
    
    def get_pr_comments(self, pr_number: int) -> List[Dict]:
        """Get all comments on a PR (issue comments and review comments).
        
        Args:
            pr_number: Pull request number
            
        Returns:
            List of comment dicts
        """
        comments = []
        
        try:
            # Get issue comments
            url = f"{self.base_url}/repos/{self.repo}/issues/{pr_number}/comments"
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            comments.extend(response.json())
            
            # Get review comments (on code lines)
            url = f"{self.base_url}/repos/{self.repo}/pulls/{pr_number}/comments"
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            comments.extend(response.json())
            
            return comments
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching comments for PR #{pr_number}: {e}")
            return comments
    
    def is_pr_approved(self, pr_number: int) -> bool:
        """Check if PR has been approved by human reviewers.
        
        Args:
            pr_number: Pull request number
            
        Returns:
            True if PR has at least one approval
        """
        reviews = self.get_pr_reviews(pr_number)
        
        # Check for approvals (excluding bots)
        for review in reviews:
            user = review.get('user', {})
            if (review.get('state') == 'APPROVED' and
                not user.get('login', '').endswith('[bot]')):
                return True
        
        return False
    
    def get_pr_status(self, pr_number: int) -> Dict:
        """Get comprehensive PR status including checks, reviews, and mergeable state.
        
        Args:
            pr_number: Pull request number
            
        Returns:
            Dict with PR status information
        """
        pr = self._get_pr(pr_number)
        if not pr:
            return {'error': 'PR not found'}
        
        # Get check runs
        checks_passed = self._check_ci_status(pr_number)
        
        return {
            'number': pr_number,
            'state': pr.get('state'),
            'draft': pr.get('draft'),
            'mergeable': pr.get('mergeable'),
            'mergeable_state': pr.get('mergeable_state'),
            'checks_passed': checks_passed,
            'approved': self.is_pr_approved(pr_number),
            'title': pr.get('title'),
            'created_at': pr.get('created_at'),
            'updated_at': pr.get('updated_at'),
        }
    
    def _check_ci_status(self, pr_number: int) -> bool:
        """Check if CI checks have passed.
        
        Args:
            pr_number: Pull request number
            
        Returns:
            True if all checks passed
        """
        try:
            pr = self._get_pr(pr_number)
            if not pr:
                return False
            
            # Get commit SHA
            head_sha = pr.get('head', {}).get('sha')
            if not head_sha:
                return False
            
            # Get check runs for this commit
            url = f"{self.base_url}/repos/{self.repo}/commits/{head_sha}/check-runs"
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            check_runs = response.json().get('check_runs', [])
            
            # All checks must be successful
            for check in check_runs:
                if check.get('conclusion') not in ['success', 'neutral', 'skipped']:
                    logger.debug(
                        f"Check '{check.get('name')}' failed: {check.get('conclusion')}"
                    )
                    return False
            
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error checking CI status for PR #{pr_number}: {e}")
            return False


# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Example: Monitor a PR
    monitor = PRMonitor(
        github_token=os.getenv("GITHUB_TOKEN", ""),
        repo=os.getenv("GITHUB_REPO", "owner/repo"),
        perplexity_timeout_minutes=10,
        poll_interval_seconds=30
    )
    
    # Wait for reviews
    pr_number = 522
    status = monitor.wait_for_reviews(pr_number)
    
    print(f"\n{'='*60}")
    print(f"Review Status for PR #{pr_number}")
    print(f"{'='*60}")
    print(f"Copilot Complete: {status.copilot_complete}")
    print(f"Perplexity Complete: {status.perplexity_complete}")
    print(f"Perplexity Failed: {status.perplexity_failed}")
    print(f"Perplexity Timeout: {status.perplexity_timeout}")
    print(f"All Reviews Complete: {status.all_reviews_complete}")
    if status.error:
        print(f"Error: {status.error}")
    print(f"{'='*60}\n")
    
    # Get PR status
    pr_status = monitor.get_pr_status(pr_number)
    print(f"PR Status: {pr_status}")
