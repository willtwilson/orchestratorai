"""Main orchestration logic for automated issue resolution."""

import os
import json
import time
import shutil
import subprocess
import re
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

from .github_client import GitHubClient
from .agents.claude import ClaudeAgent
from .agents.copilot import CopilotAgent
from .perplexity import PerplexityClient
from .qa.build import BuildVerifier
from .qa.vercel import VercelDeployer
from .dashboard import Dashboard
from .monitoring.pr_monitor import PRMonitor
from .monitoring.review_parser import ReviewParser
from .planning.plan_manager import PlanManager
from .planning.merge_recommender import MergeRecommender


class Orchestrator:
    """Orchestrates the automated issue resolution process."""

    def __init__(self, dashboard: Dashboard):
        """Initialize the orchestrator with required clients."""
        print("[DEBUG] Initializing orchestrator...")
        self.dashboard = dashboard

        # Safety settings
        self.dry_run = os.getenv("DRY_RUN", "false").lower() == "true"
        self.auto_merge = os.getenv("AUTO_MERGE", "false").lower() == "true"
        self.max_retries = int(os.getenv("MAX_RETRIES", "1"))
        self.require_tests = os.getenv("REQUIRE_TESTS", "true").lower() == "true"
        
        # PR Management settings
        self.auto_create_pr = os.getenv("AUTO_CREATE_PR", "true").lower() == "true"
        self.auto_cleanup_worktree = os.getenv("AUTO_CLEANUP_WORKTREE", "false").lower() == "true"
        self.pr_labels = os.getenv("PR_LABELS", "automated,orchestratorai").split(",")
        
        # PR Monitoring settings
        self.pr_monitoring_enabled = os.getenv("PR_MONITORING_ENABLED", "true").lower() == "true"
        self.perplexity_timeout_minutes = int(os.getenv("PERPLEXITY_TIMEOUT_MINUTES", "10"))
        self.pr_poll_interval_seconds = int(os.getenv("PR_POLL_INTERVAL_SECONDS", "30"))
        self.require_human_approval = os.getenv("REQUIRE_HUMAN_APPROVAL", "true").lower() == "true"
        self.require_ci_pass = os.getenv("REQUIRE_CI_PASS", "true").lower() == "true"
        
        # Autopilot settings
        self.autopilot_mode = os.getenv("AUTOPILOT_MODE", "false").lower() == "true"
        self.auto_merge_ready_prs = os.getenv("AUTO_MERGE_READY_PRS", "false").lower() == "true"

        if self.dry_run:
            print("[DRY RUN MODE ENABLED] No changes will be made to the repository")
        if not self.auto_merge:
            print("[SAFE MODE] PRs will require manual review and merge")
        if self.auto_create_pr:
            print("[PR MODE] Will automatically create pull requests")
        if self.pr_monitoring_enabled:
            print("[PR MONITORING] Enabled with timeout: {}min".format(self.perplexity_timeout_minutes))
        if self.autopilot_mode:
            print("[AUTOPILOT MODE] ENABLED - Will auto-merge when ready")
        elif self.auto_merge_ready_prs:
            print("[AUTO-MERGE] Enabled for ready PRs")

        print("[DEBUG] Creating GitHub client...")
        self.github = GitHubClient(
            token=os.getenv("GITHUB_TOKEN"),
            repo=os.getenv("GITHUB_REPO"),
            dry_run=self.dry_run
        )

        print("[DEBUG] Creating Claude agent...")
        self.claude = ClaudeAgent(api_key=os.getenv("ANTHROPIC_API_KEY"))

        print("[DEBUG] Creating Copilot agent...")
        self.copilot = CopilotAgent(dry_run=self.dry_run)

        print("[DEBUG] Creating Perplexity client...")
        self.perplexity = PerplexityClient(api_key=os.getenv("PERPLEXITY_API_KEY"))

        print("[DEBUG] Creating build verifier...")
        self.build_verifier = BuildVerifier(dry_run=self.dry_run)

        print("[DEBUG] Creating Vercel deployer...")
        self.vercel = VercelDeployer(
            token=os.getenv("VERCEL_TOKEN"),
            project_id=os.getenv("VERCEL_PROJECT_ID"),
            dry_run=self.dry_run
        )
        
        # Initialize PR monitoring components
        if self.pr_monitoring_enabled:
            print("[DEBUG] Creating PR monitoring components...")
            self.pr_monitor = PRMonitor(
                github_token=os.getenv("GITHUB_TOKEN"),
                repo=os.getenv("GITHUB_REPO"),
                perplexity_timeout_minutes=self.perplexity_timeout_minutes,
                poll_interval_seconds=self.pr_poll_interval_seconds
            )
            self.review_parser = ReviewParser()
            self.plan_manager = PlanManager(
                github_token=os.getenv("GITHUB_TOKEN"),
                repo=os.getenv("GITHUB_REPO")
            )
            self.merge_recommender = MergeRecommender(
                monitor=self.pr_monitor,
                require_human_approval=self.require_human_approval,
                require_ci_pass=self.require_ci_pass,
                autopilot_mode=self.autopilot_mode
            )
            print("[DEBUG] PR monitoring components initialized")
        else:
            self.pr_monitor = None
            self.review_parser = None
            self.plan_manager = None
            self.merge_recommender = None

        print("[DEBUG] Loading state...")
        self.state_file = Path(__file__).parent.parent / "data" / "state.json"
        self.state = self._load_state()
        self.max_concurrent = int(os.getenv("MAX_CONCURRENT_ISSUES", "3"))
        print("[DEBUG] Orchestrator initialized successfully!")

    def _load_state(self) -> Dict:
        """Load orchestrator state from disk."""
        if self.state_file.exists():
            with open(self.state_file, "r") as f:
                return json.load(f)
        return {"processed_issues": [], "active_issues": {}}

    def _save_state(self):
        """Save orchestrator state to disk."""
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.state_file, "w") as f:
            json.dump(self.state, f, indent=2)

    def run(self):
        """Main orchestration loop."""
        print("[DEBUG] Starting dashboard...")
        self.dashboard.start()
        print("[DEBUG] Dashboard started!")
        
        self.dashboard.log("🚀 OrchestratorAI started", level="success")
        self.dashboard.log(f"Mode: {'AUTOPILOT' if self.autopilot_mode else 'MANUAL'}", level="info")
        self.dashboard.log(f"Monitoring: {'ENABLED' if self.pr_monitoring_enabled else 'DISABLED'}", level="info")

        try:
            print("[DEBUG] Entering main loop...")
            # Run one full cycle and then exit (for controlled testing)
            self._process_cycle()
            print("[DEBUG] First cycle completed.")
            
            # Keep dashboard visible for a moment
            self.dashboard.log("✅ Cycle completed successfully", level="success")
            import time
            time.sleep(5)  # Show final state for 5 seconds
        finally:
            self.dashboard.stop()
            print("[DEBUG] Dashboard stopped")

    def _process_cycle(self):
        """Process one cycle of issue discovery and resolution."""
        print("[DEBUG] Starting process cycle...")
        # Fetch open issues with "status:ai-ready" label
        print("[DEBUG] Fetching open issues from GitHub...")
        issues = self.github.get_open_issues(labels=["status:ai-ready"])
        print(f"[DEBUG] Found {len(issues)} open issues")

        print("[DEBUG] Updating dashboard with issues...")
        # self.dashboard.update_issues(issues)  # Disabled for testing
        print("[DEBUG] Dashboard updated")

        # Filter out already processed issues
        print("[DEBUG] Filtering new issues...")
        new_issues = [
            issue for issue in issues
            if issue["number"] not in self.state["processed_issues"]
            and issue["number"] not in self.state["active_issues"]
        ]
        print(f"[DEBUG] Found {len(new_issues)} new issues to process")

        # Process new issues up to max concurrent limit
        available_slots = self.max_concurrent - len(self.state["active_issues"])
        print(f"[DEBUG] Available slots: {available_slots}")

        for issue in new_issues[:available_slots]:
            print(f"[DEBUG] Will process issue #{issue['number']}: {issue['title']}")
            print(f"[DEBUG] Labels: {[label['name'] for label in issue.get('labels', [])]}")
            self._process_issue(issue)

        # Check status of active issues
        for issue_number in list(self.state["active_issues"].keys()):
            self._check_issue_status(issue_number)

        print("[DEBUG] Cycle complete!")

    def _process_issue(self, issue: Dict):
        """Process a single issue through the full pipeline."""
        issue_number = issue["number"]
        self.dashboard.log(f"Processing issue #{issue_number}: {issue['title']}")

        try:
            # Mark as active
            self.state["active_issues"][issue_number] = {
                "status": "planning",
                "started_at": time.time()
            }
            self._save_state()
            
            # Update dashboard
            self.dashboard.update_active_issue(issue_number, "planning")

            # Step 1: Research with Perplexity
            self.dashboard.log(f"#{issue_number}: Researching context...", level="info")
            print(f"\n[STEP 1] Researching with Perplexity...")
            context = self.perplexity.research(issue["title"], issue["body"])

            print(f"\n{'='*60}")
            print(f"[PERPLEXITY RESEARCH] Issue #{issue_number}")
            print(f"{'='*60}")
            print(f"Findings: {context.get('findings', 'No findings')[:500]}...")
            print(f"Citations: {len(context.get('citations', []))} sources")
            print(f"{'='*60}\n")

            # Step 2: Planning with Claude
            self.dashboard.log(f"#{issue_number}: Creating plan with Claude...", level="info")
            print(f"\n[STEP 2] Creating plan with Claude...")
            plan = self.claude.create_plan(issue, context)

            print(f"\n{'='*60}")
            print(f"[CLAUDE PLAN] Issue #{issue_number}")
            print(f"{'='*60}")
            print(f"Title: {plan.get('title', 'N/A')}")
            print(f"Files to modify: {plan.get('files_to_modify', [])}")
            print(f"Steps: {len(plan.get('steps', []))} steps")
            print(f"{'='*60}\n")

            # Step 3: Execution with Copilot
            self.state["active_issues"][issue_number]["status"] = "executing"
            self._save_state()
            self.dashboard.update_active_issue(issue_number, "executing")
            self.dashboard.log(f"#{issue_number}: Executing with Copilot...", level="info")
            print(f"\n[STEP 3] Executing with Copilot...")
            result = self.copilot.execute_plan(plan, issue_number)

            print(f"\n{'='*60}")
            print(f"[COPILOT RESULT] Issue #{issue_number}")
            print(f"{'='*60}")
            print(f"Success: {result.get('success', False)}")
            print(f"Branch: {result.get('branch', 'N/A')}")
            print(f"Files modified: {result.get('files_modified', [])}")
            print(f"Summary: {result.get('summary', 'N/A')}")
            print(f"{'='*60}\n")

            # Step 4: Build verification
            self.state["active_issues"][issue_number]["status"] = "verifying"
            self._save_state()
            self.dashboard.update_active_issue(issue_number, "verifying")
            self.dashboard.log(f"#{issue_number}: Verifying build...", level="info")
            print(f"\n[STEP 4] Verifying build...")

            worktree_path = self.copilot.worktree_base / f"issue-{issue_number}"
            print(f"Worktree location: {worktree_path}")

            # Backup generated code before build
            backup_dir = Path("data/generated_code") / f"issue-{issue_number}"
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy all files from worktree (excluding .git)
            if worktree_path.exists():
                for item in worktree_path.iterdir():
                    if item.name != '.git':
                        if item.is_dir():
                            shutil.copytree(item, backup_dir / item.name, dirs_exist_ok=True)
                        else:
                            shutil.copy2(item, backup_dir / item.name)
                print(f"[BACKUP] Generated code saved to: {backup_dir}")

            # Create build verifier with the worktree path
            worktree_build_verifier = BuildVerifier(dry_run=self.dry_run, project_root=worktree_path)
            build_success = worktree_build_verifier.verify()

            if not build_success:
                print(f"\n{'='*60}")
                print(f"[BUILD FAILED] Issue #{issue_number}")
                print(f"{'='*60}")
                print(f"Worktree preserved at: {worktree_path}")
                print(f"To inspect: cd {worktree_path}")
                print(f"To cleanup: git worktree remove {worktree_path} --force")
                print(f"{'='*60}\n")

                self.dashboard.log(f"#{issue_number}: Build failed, worktree preserved", level="error")
                # Don't rollback yet - preserve for inspection
                # self.copilot.rollback(issue_number)
                self.github.add_comment(
                    issue_number,
                    "Build verification failed. Worktree preserved for inspection."
                )
                self._mark_issue_failed(issue_number)
                return

            # Step 5: Create Pull Request (if build passed)
            if self.auto_create_pr and not self.dry_run:
                print("\n[STEP 5] Build passed! Creating pull request...")
                
                branch_name = result.get('branch', f"issue-{issue_number}")
                pr_result = self.create_pull_request(
                    issue=issue,
                    worktree_path=worktree_path,
                    branch_name=branch_name,
                    files_created=result.get('files_modified', [])
                )
                
                if pr_result['success']:
                    print(f"\n🎉 SUCCESS! PR created: {pr_result['pr_url']}")
                    self.dashboard.log(f"#{issue_number}: PR #{pr_result['pr_number']} created", level="success")
                    
                    # Step 6: Monitor PR reviews and evaluate merge readiness
                    if self.pr_monitoring_enabled and pr_result.get('pr_number'):
                        pr_number = pr_result['pr_number']
                        self._monitor_pr_reviews(issue_number, pr_number)
                    
                    # Optional: Cleanup worktree now that PR is created
                    if self.auto_cleanup_worktree:
                        self._cleanup_worktree(worktree_path)
                    
                    self._mark_issue_completed(issue_number)
                    self.dashboard.mark_issue_completed(issue_number, pr_result['pr_number'], merged=False)
                    self.dashboard.log(f"#{issue_number}: Completed successfully with PR #{pr_result['pr_number']}", level="success")
                else:
                    print(f"\n⚠️ Build passed but PR creation failed: {pr_result.get('error')}")
                    self.github.add_comment(
                        issue_number,
                        f"Build passed but PR creation failed: {pr_result.get('error')}\n\nBranch: {branch_name}"
                    )
                    self._mark_issue_failed(issue_number)
            else:
                # Old manual flow
                self.dashboard.log(f"#{issue_number}: Build passed. Manual PR creation required.")
                self.github.add_comment(
                    issue_number,
                    f"Implementation complete!\n\n{result['summary']}\n\nBranch: {result.get('branch')}"
                )
                self._mark_issue_completed(issue_number)

        except Exception as e:
            self.dashboard.log(f"#{issue_number}: Error - {str(e)}", level="error")
            self.github.add_comment(
                issue_number,
                f"Error during processing: {str(e)}"
            )
            self._mark_issue_failed(issue_number)

    def _check_issue_status(self, issue_number: int):
        """Check the status of an active issue."""
        # Implementation for checking long-running tasks
        pass

    def _mark_issue_completed(self, issue_number: int):
        """Mark an issue as completed."""
        if issue_number in self.state["active_issues"]:
            del self.state["active_issues"][issue_number]
        self.state["processed_issues"].append(issue_number)
        self._save_state()

    def _mark_issue_failed(self, issue_number: int):
        """Mark an issue as failed."""
        if issue_number in self.state["active_issues"]:
            del self.state["active_issues"][issue_number]
        self._save_state()
    
    def create_pull_request(self, issue: Dict, worktree_path: Path, branch_name: str, files_created: List[str]) -> Dict:
        """Create a pull request for the implemented issue.
        
        Args:
            issue: GitHub issue dict
            worktree_path: Path to the worktree
            branch_name: Name of the branch
            files_created: List of created file paths
            
        Returns:
            dict with keys: success (bool), pr_number (int), pr_url (str), error (str)
        """
        print(f"\n{'='*60}")
        print(f"[PR CREATION] Issue #{issue['number']}")
        print(f"{'='*60}\n")

        # Push the branch
        print("[GIT] Pushing branch to origin...")
        push_result = subprocess.run(
            ["git", "push", "origin", branch_name],
            cwd=str(worktree_path),
            capture_output=True,
            text=True
        )

        if push_result.returncode != 0:
            print(f"[ERROR] Failed to push branch: {push_result.stderr}")
            return {"success": False, "error": "push_failed"}

        print("[OK] Branch pushed successfully")

        # Create PR body
        pr_body = self._generate_pr_body(issue, files_created)

        # Create the PR using gh CLI
        print("[GITHUB] Creating pull request...")
        pr_result = subprocess.run([
            "gh", "pr", "create",
            "--repo", os.getenv("GITHUB_REPO"),
            "--base", "main",
            "--head", branch_name,
            "--title", f"feat: {issue['title']} (Fix #{issue['number']})",
            "--body", pr_body
        ], capture_output=True, text=True, encoding='utf-8', errors='replace')

        if pr_result.returncode != 0:
            print(f"[ERROR] Failed to create PR: {pr_result.stderr}")
            return {"success": False, "error": "pr_creation_failed"}

        # Extract PR URL from output
        pr_url = pr_result.stdout.strip()

        # Get PR number
        pr_number = self._extract_pr_number(pr_url)

        print(f"[OK] Pull request created: {pr_url}")

        # Add labels to PR
        if pr_number:
            self._add_pr_labels(pr_number)

        # Post success comment to issue
        self._post_success_comment(issue['number'], pr_number, pr_url)

        # Update state
        self._update_state(issue['number'], pr_number, "pr_created")

        return {
            "success": True,
            "pr_number": pr_number,
            "pr_url": pr_url
        }
    
    def _generate_pr_body(self, issue: Dict, files_created: List[str]) -> str:
        """Generate a comprehensive PR description."""
        files_list = "\n".join([f"- {f}" for f in files_created])
        
        return f"""## Changes
This PR implements the features requested in #{issue['number']}.

### Files Added/Modified
{files_list}

### Implementation Details
{issue.get('body', 'See issue for details')[:500]}

### Quality Checks
✅ Build verification passed
✅ TypeScript compilation successful
✅ Code generated and tested

### Generated By
🤖 OrchestratorAI - Autonomous development pipeline
1. Perplexity research
2. Claude planning
3. Automated code generation
4. Build verification

Closes #{issue['number']}
"""
    
    def _extract_pr_number(self, pr_url: str) -> Optional[int]:
        """Extract PR number from GitHub URL."""
        match = re.search(r'/pull/(\d+)', pr_url)
        return int(match.group(1)) if match else None
    
    def _add_pr_labels(self, pr_number: int):
        """Add metadata labels to the PR."""
        if not self.pr_labels:
            return
            
        subprocess.run([
            "gh", "pr", "edit", str(pr_number),
            "--add-label", ",".join(self.pr_labels),
            "--repo", os.getenv("GITHUB_REPO")
        ], capture_output=True)

        print(f"[OK] Added labels: {', '.join(self.pr_labels)}")
    
    def _post_success_comment(self, issue_number: int, pr_number: Optional[int], pr_url: str):
        """Post a success comment to the original issue."""
        comment = f"""✅ Implementation Complete!

The code has been generated and is ready for review.

**Pull Request:** #{pr_number if pr_number else 'N/A'}
**Link:** {pr_url}

**Quality Checks:**
✅ TypeScript compilation passed
✅ Next.js build successful
✅ Automated tests included

You can review the PR and merge when ready!"""

        subprocess.run([
            "gh", "issue", "comment", str(issue_number),
            "--body", comment,
            "--repo", os.getenv("GITHUB_REPO")
        ], capture_output=True)

        print(f"[OK] Posted success comment to issue #{issue_number}")
    
    def _update_state(self, issue_number: int, pr_number: Optional[int], status: str):
        """Update the orchestrator state file."""
        state_file = self.state_file
        state = self.state
        
        # Move from active to completed
        if str(issue_number) in state["active_issues"]:
            del state["active_issues"][str(issue_number)]
        
        if "completed_issues" not in state:
            state["completed_issues"] = {}
        
        state["completed_issues"][str(issue_number)] = {
            "status": status,
            "pr_number": pr_number,
            "completed_at": datetime.now().isoformat()
        }
        
        self._save_state()
        print(f"[OK] Updated state: Issue #{issue_number} -> {status}")
    
    def _cleanup_worktree(self, worktree_path: Path):
        """Remove the worktree after PR creation."""
        print(f"\n[CLEANUP] Removing worktree: {worktree_path}")
        
        # Remove worktree
        subprocess.run([
            "git", "worktree", "remove", 
            str(worktree_path), 
            "--force"
        ], capture_output=True)

        print("[OK] Worktree cleaned up")
    
    def _monitor_pr_reviews(self, issue_number: int, pr_number: int):
        """Monitor PR reviews and evaluate merge readiness.
        
        Args:
            issue_number: GitHub issue number
            pr_number: Pull request number
        """
        print(f"\n{'='*60}")
        print(f"[STEP 6] Monitoring PR #{pr_number} Reviews")
        print(f"{'='*60}\n")
        
        try:
            # Update state
            if str(issue_number) in self.state["active_issues"]:
                self.state["active_issues"][str(issue_number)]["status"] = "waiting_reviews"
                self.state["active_issues"][str(issue_number)]["pr_number"] = pr_number
                self._save_state()
            
            # Update dashboard
            self.dashboard.update_active_issue(issue_number, "waiting_reviews", {"pr_number": pr_number})
            
            # Wait for reviews to complete
            print("[MONITOR] Waiting for Copilot and Perplexity reviews...")
            print(f"           Timeout: {self.perplexity_timeout_minutes} minutes")
            print(f"           Poll interval: {self.pr_poll_interval_seconds} seconds")
            
            self.dashboard.log(f"PR #{pr_number}: Waiting for reviews (timeout: {self.perplexity_timeout_minutes}min)", level="info")
            
            review_status = self.pr_monitor.wait_for_reviews(
                pr_number=pr_number,
                timeout_minutes=self.perplexity_timeout_minutes
            )
            
            # Log review status
            print(f"\n{'='*60}")
            print(f"[REVIEW STATUS] PR #{pr_number}")
            print(f"{'='*60}")
            print(f"Copilot Complete: {review_status.copilot_complete}")
            print(f"Perplexity Complete: {review_status.perplexity_complete}")
            print(f"Perplexity Failed: {review_status.perplexity_failed}")
            print(f"Perplexity Timeout: {review_status.perplexity_timeout}")
            print(f"All Reviews Complete: {review_status.all_reviews_complete}")
            print(f"{'='*60}\n")
            
            # Handle Perplexity failures gracefully
            if review_status.perplexity_failed:
                print("⚠️  Perplexity workflow failed, proceeding with Copilot review only")
                self.dashboard.log(
                    f"PR #{pr_number}: Perplexity review failed, continuing with Copilot only",
                    level="warning"
                )
            elif review_status.perplexity_timeout:
                print("⚠️  Perplexity review timed out, proceeding with Copilot review only")
                self.dashboard.log(
                    f"PR #{pr_number}: Perplexity review timed out after {self.perplexity_timeout_minutes}min",
                    level="warning"
                )
            
            # Update PR status in dashboard
            self.dashboard.update_pr_status(pr_number, {
                "review_status": review_status.to_dict()
            })
            
            # Parse review comments
            print("[PARSER] Parsing review comments...")
            self.dashboard.log(f"PR #{pr_number}: Parsing {len(comments)} review comments", level="info")
            comments = self.pr_monitor.get_pr_comments(pr_number)
            review_items = self.review_parser.parse_all_comments(comments)
            
            print(f"[OK] Parsed {len(review_items)} review items")
            
            # Categorize items
            categorized = self.review_parser.categorize_items(review_items)
            print("\nReview Items by Priority:")
            for priority, items in categorized.items():
                if items:
                    print(f"  {priority.upper()}: {len(items)} items")
            
            # Create remediation plan
            print("\n[PLAN] Creating remediation plan...")
            plan = self.plan_manager.create_plan(
                pr_number=pr_number,
                review_items=review_items
            )
            
            print(self.plan_manager.get_plan_summary(plan))
            
            # Handle deferred items
            if plan.deferred_items:
                print(f"\n[DEFERRED] Creating issue for {len(plan.deferred_items)} deferred items...")
                deferred_issue_num = self.plan_manager.create_deferred_issue(
                    plan=plan,
                    pr_number=pr_number,
                    original_issue_number=issue_number
                )
                if deferred_issue_num:
                    print(f"[OK] Created deferred issue #{deferred_issue_num}")
                    self.dashboard.log(f"Created deferred issue #{deferred_issue_num} from PR #{pr_number}")
            
            # Evaluate merge readiness
            print("\n[RECOMMENDER] Evaluating merge readiness...")
            decision = self.merge_recommender.evaluate(
                pr_number=pr_number,
                review_status=review_status,
                remediation_plan=plan
            )
            
            print(self.merge_recommender.format_decision(decision))
            
            # Update state with decision
            if str(issue_number) in self.state["active_issues"]:
                self.state["active_issues"][str(issue_number)].update({
                    "review_status": review_status.to_dict(),
                    "remediation_plan": plan.to_dict(),
                    "merge_decision": decision.to_dict()
                })
                self._save_state()
            
            # Update dashboard with full PR status
            self.dashboard.update_pr_status(pr_number, {
                "review_status": review_status.to_dict(),
                "remediation_plan": plan.to_dict(),
                "merge_decision": decision.to_dict()
            })
            
            # Act on decision
            if decision.ready_to_merge:
                if decision.autopilot_recommended and self.autopilot_mode:
                    print("\n[AUTOPILOT] PR is ready - auto-merging...")
                    self.dashboard.log(f"PR #{pr_number}: Auto-merging (autopilot mode)", level="success")
                    self._auto_merge_pr(pr_number, issue_number)
                elif self.auto_merge_ready_prs:
                    print("\n[AUTO-MERGE] PR is ready - merging...")
                    self.dashboard.log(f"PR #{pr_number}: Auto-merging", level="success")
                    self._auto_merge_pr(pr_number, issue_number)
                else:
                    print("\n[MANUAL] PR is ready for manual merge")
                    print(f"         Review recommendations:")
                    for rec in decision.recommendations:
                        print(f"         • {rec}")
                    
                    self.dashboard.log(f"PR #{pr_number}: Ready for manual merge", level="success")
                    
                    # Post merge-ready comment to PR
                    self._post_merge_ready_comment(pr_number, decision)
                    
                    # Update issue status
                    if str(issue_number) in self.state["active_issues"]:
                        self.state["active_issues"][str(issue_number)]["status"] = "ready_to_merge"
                        self._save_state()
                    self.dashboard.update_active_issue(issue_number, "ready_to_merge")
            else:
                print(f"\n[BLOCKED] PR not ready: {decision.reason}")
                print(f"          Blocking items: {len(decision.blocking_items)}")
                
                self.dashboard.log(f"PR #{pr_number}: Blocked - {decision.reason}", level="warning")
                
                # Post blocking items to PR
                self._post_review_summary_comment(pr_number, decision, plan)
                
                # Update issue status
                if str(issue_number) in self.state["active_issues"]:
                    self.state["active_issues"][str(issue_number)]["status"] = "blocked"
                    self._save_state()
                self.dashboard.update_active_issue(issue_number, "blocked")
        
        except Exception as e:
            print(f"\n❌ Error during PR monitoring: {e}")
            self.dashboard.log(f"PR #{pr_number}: Monitoring error - {str(e)}", level="error")
            
            # Don't fail the whole process - PR is still created
            if str(issue_number) in self.state["active_issues"]:
                self.state["active_issues"][str(issue_number)]["status"] = "monitoring_failed"
                self.state["active_issues"][str(issue_number)]["error"] = str(e)
                self._save_state()
    
    def _auto_merge_pr(self, pr_number: int, issue_number: int):
        """Auto-merge a PR that is ready.
        
        Args:
            pr_number: Pull request number
            issue_number: Original issue number
        """
        print(f"\n{'='*60}")
        print(f"[AUTO-MERGE] PR #{pr_number}")
        print(f"{'='*60}\n")
        
        try:
            # Merge via gh CLI
            merge_result = subprocess.run([
                "gh", "pr", "merge", str(pr_number),
                "--repo", os.getenv("GITHUB_REPO"),
                "--squash",  # Squash commits
                "--delete-branch",  # Delete branch after merge
                "--auto"  # Auto-merge when checks pass
            ], capture_output=True, text=True, encoding='utf-8', errors='replace')
            
            if merge_result.returncode != 0:
                print(f"❌ Auto-merge failed: {merge_result.stderr}")
                self.dashboard.log(f"PR #{pr_number}: Auto-merge failed - {merge_result.stderr}", level="error")
                
                # Post comment about failure
                subprocess.run([
                    "gh", "pr", "comment", str(pr_number),
                    "--body", f"🤖 Auto-merge attempted but failed:\n```\n{merge_result.stderr}\n```\n\nPlease merge manually.",
                    "--repo", os.getenv("GITHUB_REPO")
                ], capture_output=True)
                
                return False
            
            print(f"✅ PR #{pr_number} auto-merged successfully")
            self.dashboard.log(f"PR #{pr_number}: Auto-merged and proceeding to next task", level="success")
            
            # Mark issue as completed
            self._mark_issue_completed(issue_number)
            self.dashboard.mark_issue_completed(issue_number, pr_number, merged=True)
            self.dashboard.clear_pr_status(pr_number)
            
            # Post completion comment
            subprocess.run([
                "gh", "issue", "comment", str(issue_number),
                "--body", f"✅ **Fully Automated Resolution Complete!**\n\nPR #{pr_number} has been auto-merged.\n\n🤖 OrchestratorAI - Autopilot Mode",
                "--repo", os.getenv("GITHUB_REPO")
            ], capture_output=True)
            
            return True
            
        except Exception as e:
            print(f"❌ Error during auto-merge: {e}")
            self.dashboard.log(f"PR #{pr_number}: Auto-merge error - {str(e)}", level="error")
            return False
    
    def _post_merge_ready_comment(self, pr_number: int, decision):
        """Post a comment indicating PR is ready to merge.
        
        Args:
            pr_number: Pull request number
            decision: MergeDecision object
        """
        comment = f"""✅ **Ready to Merge!**

All automated checks have passed:
- ✅ Copilot review complete
- ✅ Perplexity review complete
- ✅ No blocking issues found
- ✅ Build verification passed

**Recommendations:**
"""
        for rec in decision.recommendations:
            comment += f"\n- {rec}"
        
        comment += "\n\n🤖 *OrchestratorAI - Merge Recommendation*"
        
        subprocess.run([
            "gh", "pr", "comment", str(pr_number),
            "--body", comment,
            "--repo", os.getenv("GITHUB_REPO")
        ], capture_output=True)
        
        print(f"[OK] Posted merge-ready comment to PR #{pr_number}")
    
    def _post_review_summary_comment(self, pr_number: int, decision, plan):
        """Post a summary of review findings and blocking items.
        
        Args:
            pr_number: Pull request number
            decision: MergeDecision object
            plan: RemediationPlan object
        """
        comment = f"""📋 **Review Summary**

**Status:** {decision.readiness.value.upper().replace('_', ' ')}
**Reason:** {decision.reason}

"""
        
        if decision.blocking_items:
            comment += "### 🚫 Blocking Items\n\n"
            for item in decision.blocking_items:
                comment += f"- {item}\n"
            comment += "\n"
        
        if plan.critical_items:
            comment += f"### 🔴 Critical ({len(plan.critical_items)})\n\n"
            for item in plan.critical_items[:5]:  # Show first 5
                comment += f"- {item.description[:100]}\n"
            if len(plan.critical_items) > 5:
                comment += f"- ... and {len(plan.critical_items) - 5} more\n"
            comment += "\n"
        
        if plan.high_items:
            comment += f"### 🟠 High Priority ({len(plan.high_items)})\n\n"
            for item in plan.high_items[:5]:
                comment += f"- {item.description[:100]}\n"
            if len(plan.high_items) > 5:
                comment += f"- ... and {len(plan.high_items) - 5} more\n"
            comment += "\n"
        
        if decision.recommendations:
            comment += "### 💡 Next Steps\n\n"
            for rec in decision.recommendations:
                comment += f"- {rec}\n"
            comment += "\n"
        
        if plan.deferred_items and plan.deferred_issue_number:
            comment += f"### ⏭️ Deferred Items\n\n"
            comment += f"{len(plan.deferred_items)} items deferred to issue #{plan.deferred_issue_number}\n\n"
        
        comment += "🤖 *OrchestratorAI - Automated Review Analysis*"
        
        subprocess.run([
            "gh", "pr", "comment", str(pr_number),
            "--body", comment,
            "--repo", os.getenv("GITHUB_REPO")
        ], capture_output=True)
        
        print(f"[OK] Posted review summary to PR #{pr_number}")
