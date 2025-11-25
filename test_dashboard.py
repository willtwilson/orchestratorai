"""Test the enhanced dashboard with simulated workflow."""

import time
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.dashboard import Dashboard


def simulate_issue_workflow():
    """Simulate processing an issue through the full workflow."""
    dashboard = Dashboard()
    
    # Start dashboard
    print("Starting dashboard...")
    dashboard.start()
    
    try:
        # Simulate initial state
        issues = [
            {"number": 521, "title": "Add capitalize utility function", "state": "open", "labels": [{"name": "status:ai-ready"}]},
            {"number": 520, "title": "Fix responsive layout on mobile", "state": "open", "labels": [{"name": "bug"}]},
            {"number": 519, "title": "Add dark mode support", "state": "open", "labels": [{"name": "enhancement"}]},
        ]
        
        dashboard.update_issues(issues)
        dashboard.log("OrchestratorAI started - Monitoring for issues", level="success")
        time.sleep(2)
        
        # Start processing issue #521
        dashboard.log("Found new issue #521: Add capitalize utility function", level="info")
        time.sleep(1)
        
        dashboard.update_active_issue(521, "planning")
        dashboard.log("#521: Researching context with Perplexity...", level="info")
        time.sleep(3)
        
        dashboard.log("#521: Creating plan with Claude...", level="info")
        time.sleep(2)
        
        # Executing
        dashboard.update_active_issue(521, "executing")
        dashboard.log("#521: Generating code with Copilot...", level="info")
        time.sleep(4)
        
        # Verifying
        dashboard.update_active_issue(521, "verifying")
        dashboard.log("#521: Running build verification...", level="info")
        time.sleep(3)
        
        dashboard.log("#521: Build passed successfully!", level="success")
        time.sleep(1)
        
        # PR created
        dashboard.log("#521: PR #522 created", level="success")
        time.sleep(1)
        
        # Monitoring reviews
        dashboard.update_active_issue(521, "waiting_reviews", {"pr_number": 522})
        dashboard.log("PR #522: Waiting for reviews (timeout: 10min)", level="info")
        
        # Update PR status - waiting for reviews
        dashboard.update_pr_status(522, {
            "review_status": {
                "copilot_complete": False,
                "perplexity_complete": False,
                "perplexity_failed": False
            },
            "merge_decision": {
                "readiness": "waiting_reviews"
            }
        })
        time.sleep(3)
        
        # Copilot review complete
        dashboard.log("PR #522: Copilot review completed", level="success")
        dashboard.update_pr_status(522, {
            "review_status": {
                "copilot_complete": True,
                "perplexity_complete": False,
                "perplexity_failed": False
            },
            "merge_decision": {
                "readiness": "waiting_reviews"
            }
        })
        time.sleep(2)
        
        # Perplexity review complete
        dashboard.log("PR #522: Perplexity review completed", level="success")
        dashboard.update_pr_status(522, {
            "review_status": {
                "copilot_complete": True,
                "perplexity_complete": True,
                "perplexity_failed": False
            },
            "merge_decision": {
                "readiness": "ready",
                "blocking_items": []
            }
        })
        time.sleep(2)
        
        # Parse reviews
        dashboard.log("PR #522: Parsing 12 review comments", level="info")
        time.sleep(1)
        
        dashboard.log("PR #522: Created remediation plan (0 critical, 2 medium, 1 low)", level="info")
        time.sleep(1)
        
        # Ready to merge
        dashboard.update_active_issue(521, "ready_to_merge")
        dashboard.log("PR #522: Ready for manual merge", level="success")
        time.sleep(3)
        
        # Simulate starting another issue
        dashboard.log("Found new issue #520: Fix responsive layout", level="info")
        dashboard.update_active_issue(520, "planning")
        time.sleep(2)
        
        # Simulate completion of #521 (manual merge)
        dashboard.log("PR #522: Manually merged by user", level="success")
        dashboard.mark_issue_completed(521, pr_number=522, merged=False)
        dashboard.clear_pr_status(522)
        time.sleep(2)
        
        # Continue with #520
        dashboard.update_active_issue(520, "executing")
        dashboard.log("#520: Generating code...", level="info")
        time.sleep(3)
        
        # Simulate a build failure
        dashboard.update_active_issue(520, "verifying")
        dashboard.log("#520: Running build verification...", level="info")
        time.sleep(2)
        
        dashboard.log("#520: Build failed - syntax error in generated code", level="error")
        dashboard.mark_issue_failed(520, "Build verification failed")
        time.sleep(3)
        
        # Start #519
        dashboard.log("Found new issue #519: Add dark mode support", level="info")
        dashboard.update_active_issue(519, "planning")
        time.sleep(2)
        
        dashboard.update_active_issue(519, "executing")
        time.sleep(3)
        
        dashboard.update_active_issue(519, "verifying")
        time.sleep(2)
        
        dashboard.log("#519: Build passed!", level="success")
        dashboard.log("#519: PR #523 created", level="success")
        time.sleep(1)
        
        # Autopilot mode - auto merge
        dashboard.update_active_issue(519, "waiting_reviews", {"pr_number": 523})
        dashboard.update_pr_status(523, {
            "review_status": {
                "copilot_complete": True,
                "perplexity_complete": True,
                "perplexity_failed": False
            },
            "merge_decision": {
                "readiness": "ready",
                "blocking_items": []
            }
        })
        time.sleep(2)
        
        dashboard.log("PR #523: Auto-merging (autopilot mode)", level="success")
        time.sleep(1)
        
        dashboard.log("PR #523: Auto-merged successfully!", level="success")
        dashboard.mark_issue_completed(519, pr_number=523, merged=True)
        dashboard.clear_pr_status(523)
        time.sleep(3)
        
        # Show final stats
        stats = dashboard.get_stats()
        dashboard.log(f"Session complete - Processed: {stats['total_processed']}, Merged: {stats['total_merged']}, Failed: {stats['total_failed']}", level="success")
        time.sleep(5)
        
    finally:
        dashboard.stop()
        print("\nDashboard stopped")


if __name__ == "__main__":
    print("="*70)
    print("  ENHANCED DASHBOARD - SIMULATION TEST")
    print("="*70)
    print("\nThis will simulate a full workflow with the enhanced dashboard.")
    print("Watch the real-time updates!\n")
    
    # Auto-start for testing
    print("Starting in 2 seconds...")
    time.sleep(2)
    
    simulate_issue_workflow()
    
    print("\n" + "="*70)
    print("  SIMULATION COMPLETE")
    print("="*70)
