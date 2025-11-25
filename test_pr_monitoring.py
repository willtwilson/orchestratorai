"""End-to-end test of PR monitoring system on real PR #522.

This script tests the complete workflow:
1. Monitor PR reviews (Copilot + Perplexity)
2. Parse review comments
3. Create remediation plan
4. Handle deferred items
5. Evaluate merge readiness
6. Generate recommendations

Run: python -m test_pr_monitoring
"""

import os
import sys
import logging
from pathlib import Path
from datetime import datetime

from src.monitoring.pr_monitor import PRMonitor, ReviewStatus
from src.monitoring.review_parser import ReviewParser, ReviewPriority
from src.planning.plan_manager import PlanManager
from src.planning.merge_recommender import MergeRecommender

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_pr_monitoring_e2e.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def print_section(title: str):
    """Print a section header."""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")


def test_pr_522():
    """Run end-to-end test on PR #522."""
    
    print_section("E2E TEST: PR MONITORING SYSTEM")
    print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Target PR: #522 (Clarium repository)")
    print(f"Log File: test_pr_monitoring_e2e.log")
    
    # Load environment
    from dotenv import load_dotenv
    load_dotenv()
    
    github_token = os.getenv("GITHUB_TOKEN")
    github_repo = os.getenv("GITHUB_REPO", "willtwilson/clarium")
    
    if not github_token:
        print("❌ ERROR: GITHUB_TOKEN not found in .env")
        return False
    
    print(f"\n✓ Environment loaded")
    print(f"  Repository: {github_repo}")
    
    # Phase 1: Initialize components
    print_section("PHASE 1: Initialize Components")
    
    try:
        monitor = PRMonitor(
            github_token=github_token,
            repo=github_repo,
            perplexity_timeout_minutes=5,  # Shorter timeout for testing
            poll_interval_seconds=10
        )
        print("✓ PRMonitor initialized")
        
        parser = ReviewParser()
        print("✓ ReviewParser initialized")
        
        plan_manager = PlanManager(
            github_token=github_token,
            repo=github_repo
        )
        print("✓ PlanManager initialized")
        
        recommender = MergeRecommender(
            monitor=monitor,
            require_human_approval=False,  # For testing
            require_ci_pass=False,  # PR may have build issues
            autopilot_mode=False
        )
        print("✓ MergeRecommender initialized")
        
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        logger.error(f"Initialization error: {e}", exc_info=True)
        return False
    
    # Phase 2: Get PR status
    print_section("PHASE 2: Get PR #522 Status")
    
    try:
        pr_status = monitor.get_pr_status(522)
        
        if 'error' in pr_status:
            print(f"❌ Could not fetch PR: {pr_status['error']}")
            return False
        
        print(f"✓ PR Found: {pr_status['title']}")
        print(f"  State: {pr_status['state']}")
        print(f"  Draft: {pr_status.get('draft', 'unknown')}")
        print(f"  Mergeable: {pr_status.get('mergeable', 'unknown')}")
        print(f"  Approved: {pr_status.get('approved', 'unknown')}")
        print(f"  CI Checks: {pr_status.get('checks_passed', 'unknown')}")
        
    except Exception as e:
        print(f"❌ Failed to get PR status: {e}")
        logger.error(f"PR status error: {e}", exc_info=True)
        return False
    
    # Phase 3: Check for existing reviews (don't wait)
    print_section("PHASE 3: Check Existing Reviews")
    
    try:
        # Get existing comments without waiting
        comments = monitor.get_pr_comments(522)
        print(f"✓ Found {len(comments)} total comments/reviews")
        
        # Check for Copilot
        copilot_found = monitor._check_copilot_review(522)
        print(f"  Copilot review: {'✓ Found' if copilot_found else '✗ Not found'}")
        
        # Check for Perplexity
        perplexity_found, workflow_failed = monitor._check_perplexity_review(522)
        if perplexity_found:
            print(f"  Perplexity review: ✓ Found")
        elif workflow_failed:
            print(f"  Perplexity review: ⚠️ Workflow failed/timed out")
        else:
            print(f"  Perplexity review: ⏳ Not found (may still be running)")
        
        # Create review status from existing data
        review_status = ReviewStatus(
            pr_number=522,
            copilot_complete=copilot_found,
            perplexity_complete=perplexity_found,
            perplexity_failed=workflow_failed and not perplexity_found,
            all_reviews_complete=copilot_found or perplexity_found
        )
        
    except Exception as e:
        print(f"❌ Failed to check reviews: {e}")
        logger.error(f"Review check error: {e}", exc_info=True)
        return False
    
    # Phase 4: Parse review comments
    print_section("PHASE 4: Parse Review Comments")
    
    try:
        review_items = parser.parse_all_comments(comments)
        print(f"✓ Parsed {len(review_items)} review items")
        
        # Categorize
        categorized = parser.categorize_items(review_items)
        
        print("\nReview Items by Priority:")
        for priority, items in categorized.items():
            if items:
                print(f"  {priority.upper()}: {len(items)} items")
                for item in items[:3]:  # Show first 3
                    desc = item.description[:60] + "..." if len(item.description) > 60 else item.description
                    print(f"    - [{item.reviewer}] {desc}")
                if len(items) > 3:
                    print(f"    ... and {len(items) - 3} more")
        
        # Get blocking items
        blocking = parser.get_blocking_items(review_items)
        if blocking:
            print(f"\nWARNING: {len(blocking)} BLOCKING items found")
        
        # Get deferred items
        deferred = parser.get_deferred_items(review_items)
        if deferred:
            print(f"\nNOTE: {len(deferred)} items marked as DEFERRED")
        
    except Exception as e:
        print(f"❌ Failed to parse reviews: {e}")
        logger.error(f"Parse error: {e}", exc_info=True)
        return False
    
    # Phase 5: Create remediation plan
    print_section("PHASE 5: Create Remediation Plan")
    
    try:
        plan = plan_manager.create_plan(
            pr_number=522,
            review_items=review_items
        )
        
        print(plan_manager.get_plan_summary(plan))
        
        # Test deferred issue creation (DRY RUN)
        if plan.deferred_items:
            print(f"\nNOTE: Would create deferred issue with {len(plan.deferred_items)} items")
            print("   (Skipping actual creation for test)")
            # Uncomment to actually create:
            # issue_num = plan_manager.create_deferred_issue(plan, 522, 521)
            # if issue_num:
            #     print(f"✓ Created deferred issue #{issue_num}")
        
    except Exception as e:
        print(f"❌ Failed to create plan: {e}")
        logger.error(f"Plan creation error: {e}", exc_info=True)
        return False
    
    # Phase 6: Evaluate merge readiness
    print_section("PHASE 6: Evaluate Merge Readiness")
    
    try:
        decision = recommender.evaluate(
            pr_number=522,
            review_status=review_status,
            remediation_plan=plan
        )
        
        print(recommender.format_decision(decision))
        
        # Log decision details
        logger.info(f"Merge decision: {decision.to_dict()}")
        
    except Exception as e:
        print(f"❌ Failed to evaluate merge: {e}")
        logger.error(f"Merge evaluation error: {e}", exc_info=True)
        return False
    
    # Phase 7: Summary
    print_section("TEST COMPLETE - SUMMARY")
    
    print("Component Test Results:")
    print(f"  ✓ PR Monitor - Fetched PR status and reviews")
    print(f"  ✓ Review Parser - Parsed {len(review_items)} items")
    print(f"  ✓ Plan Manager - Created plan with {plan.total_items()} items")
    print(f"  ✓ Merge Recommender - Decision: {decision.readiness.value}")
    
    print(f"\nKey Metrics:")
    print(f"  Total Comments: {len(comments)}")
    print(f"  Review Items: {len(review_items)}")
    print(f"  Blocking Items: {len(blocking)}")
    print(f"  Deferred Items: {len(deferred)}")
    print(f"  Ready to Merge: {decision.ready_to_merge}")
    
    print(f"\nLog saved to: test_pr_monitoring_e2e.log")
    
    return True


if __name__ == "__main__":
    print("\n" + "="*70)
    print("  PR MONITORING SYSTEM - END-TO-END TEST")
    print("="*70 + "\n")
    
    success = test_pr_522()
    
    if success:
        print("\n" + "="*70)
        print("  SUCCESS: ALL TESTS PASSED")
        print("="*70 + "\n")
        sys.exit(0)
    else:
        print("\n" + "="*70)
        print("  FAILURE: TESTS FAILED - Check logs for details")
        print("="*70 + "\n")
        sys.exit(1)
