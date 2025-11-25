"""Rich terminal dashboard for live status monitoring."""

import time
from datetime import datetime
from typing import List, Dict, Optional, Any
from threading import Thread, Lock

from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.columns import Columns
from rich import box
from rich.align import Align


class Dashboard:
    """Live terminal dashboard using Rich with enhanced monitoring."""

    def __init__(self):
        """Initialize the dashboard."""
        self.console = Console()
        self.live = None
        self.layout = Layout()

        self.issues = []
        self.active_issues = {}  # Issue number -> detailed status
        self.completed_issues = {}
        self.pr_statuses = {}  # PR number -> review/merge status
        self.logs = []
        self.max_logs = 15
        self.lock = Lock()
        
        # Statistics
        self.stats = {
            "total_processed": 0,
            "total_failed": 0,
            "total_merged": 0,
            "avg_processing_time": 0.0
        }

        self._setup_layout()

    def _setup_layout(self):
        """Setup the dashboard layout with PR monitoring sections."""
        self.layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main"),
            Layout(name="footer", size=12)
        )

        self.layout["main"].split_row(
            Layout(name="left"),
            Layout(name="right", size=50)
        )
        
        self.layout["left"].split_column(
            Layout(name="queued", size=10),
            Layout(name="active")
        )
        
        self.layout["right"].split_column(
            Layout(name="stats", size=8),
            Layout(name="pr_status")
        )
        
        self.layout["footer"].update(self._create_logs_panel())

    def start(self):
        """Start the live dashboard."""
        self.live = Live(
            self.layout,
            console=self.console,
            refresh_per_second=2,  # Reduced to avoid flickering
            screen=False,
            vertical_overflow="visible"
        )
        self.live.start()

    def stop(self):
        """Stop the live dashboard."""
        if self.live:
            self.live.stop()

    def update_issues(self, issues: List[Dict]):
        """Update the issues list.

        Args:
            issues: List of issue dictionaries from GitHub
        """
        with self.lock:
            self.issues = issues
            self._refresh()
    
    def update_active_issue(self, issue_number: int, status: str, details: Optional[Dict] = None):
        """Update status of an active issue.
        
        Args:
            issue_number: GitHub issue number
            status: Current status (planning, executing, verifying, waiting_reviews, etc.)
            details: Additional details dict
        """
        with self.lock:
            if issue_number not in self.active_issues:
                self.active_issues[issue_number] = {
                    "started_at": datetime.now(),
                    "status": status,
                    "details": details or {}
                }
            else:
                self.active_issues[issue_number]["status"] = status
                if details:
                    self.active_issues[issue_number]["details"].update(details)
            self._refresh()
    
    def update_pr_status(self, pr_number: int, status: Dict):
        """Update PR review/merge status.
        
        Args:
            pr_number: Pull request number
            status: Status dict with review/merge info
        """
        with self.lock:
            self.pr_statuses[pr_number] = {
                **status,
                "updated_at": datetime.now()
            }
            self._refresh()
    
    def mark_issue_completed(self, issue_number: int, pr_number: Optional[int] = None, merged: bool = False):
        """Mark an issue as completed.
        
        Args:
            issue_number: GitHub issue number
            pr_number: Associated PR number
            merged: Whether the PR was auto-merged
        """
        with self.lock:
            if issue_number in self.active_issues:
                issue_data = self.active_issues[issue_number]
                started = issue_data["started_at"]
                duration = (datetime.now() - started).total_seconds()
                
                self.completed_issues[issue_number] = {
                    "completed_at": datetime.now(),
                    "duration": duration,
                    "pr_number": pr_number,
                    "merged": merged
                }
                
                del self.active_issues[issue_number]
                self.stats["total_processed"] += 1
                if merged:
                    self.stats["total_merged"] += 1
                
                # Update average processing time
                total_time = sum(c["duration"] for c in self.completed_issues.values())
                self.stats["avg_processing_time"] = total_time / len(self.completed_issues)
            
            self._refresh()
    
    def mark_issue_failed(self, issue_number: int, error: str):
        """Mark an issue as failed.
        
        Args:
            issue_number: GitHub issue number
            error: Error message
        """
        with self.lock:
            if issue_number in self.active_issues:
                del self.active_issues[issue_number]
            self.stats["total_failed"] += 1
            self.log(f"Issue #{issue_number} failed: {error}", level="error")
            self._refresh()

    def log(self, message: str, level: str = "info"):
        """Add a log message.

        Args:
            message: Log message
            level: Log level (info, warning, error, success)
        """
        with self.lock:
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.logs.append({
                "timestamp": timestamp,
                "message": message,
                "level": level
            })

            # Keep only recent logs
            if len(self.logs) > self.max_logs:
                self.logs = self.logs[-self.max_logs:]

            self._refresh()

    def _refresh(self):
        """Refresh the dashboard display."""
        if not self.live:
            return

        self.layout["header"].update(self._create_header())
        self.layout["queued"].update(self._create_queued_panel())
        self.layout["active"].update(self._create_active_panel())
        self.layout["stats"].update(self._create_stats_panel())
        self.layout["pr_status"].update(self._create_pr_status_panel())
        self.layout["footer"].update(self._create_logs_panel())

    def _create_header(self) -> Panel:
        """Create the header panel with title and time."""
        header_text = Text()
        header_text.append("🤖 ", style="bold cyan")
        header_text.append("OrchestratorAI", style="bold cyan")
        header_text.append(" - ", style="dim")
        header_text.append("Autonomous Development Pipeline", style="bold white")
        header_text.append(" | ", style="dim")
        header_text.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), style="yellow")

        return Panel(
            Align.center(header_text),
            box=box.DOUBLE,
            style="cyan"
        )
    
    def _create_queued_panel(self) -> Panel:
        """Create the queued issues panel."""
        # Filter issues that are not active
        active_nums = set(self.active_issues.keys())
        queued = [i for i in self.issues if i["number"] not in active_nums][:5]
        
        if not queued:
            content = Text("No issues queued", style="dim italic")
            return Panel(content, title="📋 Queued Issues (0)", border_style="blue", box=box.ROUNDED)
        
        table = Table(box=box.SIMPLE_HEAD, show_header=False, padding=(0, 1))
        table.add_column("#", style="cyan", width=6)
        table.add_column("Title", style="white")
        
        for issue in queued:
            table.add_row(
                f"#{issue['number']}",
                issue["title"][:45] + ("..." if len(issue["title"]) > 45 else "")
            )
        
        return Panel(
            table,
            title=f"📋 Queued Issues ({len(queued)})",
            border_style="blue",
            box=box.ROUNDED
        )
    
    def _create_active_panel(self) -> Panel:
        """Create the active issues panel with detailed status."""
        if not self.active_issues:
            content = Text("No active issues", style="dim italic")
            return Panel(content, title="⚙️  Active Issues (0)", border_style="green", box=box.ROUNDED)
        
        table = Table(box=box.SIMPLE_HEAD, show_header=True, padding=(0, 1))
        table.add_column("#", style="cyan bold", width=6)
        table.add_column("Status", style="white", width=18)
        table.add_column("Duration", style="yellow", width=10)
        table.add_column("Details", style="dim")
        
        for issue_num, issue_data in self.active_issues.items():
            status = issue_data["status"]
            started = issue_data["started_at"]
            duration = (datetime.now() - started).total_seconds()
            
            # Format duration
            if duration < 60:
                duration_str = f"{int(duration)}s"
            elif duration < 3600:
                duration_str = f"{int(duration/60)}m {int(duration%60)}s"
            else:
                duration_str = f"{int(duration/3600)}h {int((duration%3600)/60)}m"
            
            # Status with icon
            status_display = self._get_status_display(status)
            
            # Details
            details = issue_data.get("details", {})
            detail_str = ""
            if status == "waiting_reviews":
                pr_num = details.get("pr_number")
                detail_str = f"PR #{pr_num}" if pr_num else ""
            elif status == "verifying":
                detail_str = "Running build..."
            elif status == "executing":
                detail_str = "Generating code..."
            
            table.add_row(
                f"#{issue_num}",
                status_display,
                duration_str,
                detail_str
            )
        
        return Panel(
            table,
            title=f"⚙️  Active Issues ({len(self.active_issues)})",
            border_style="green",
            box=box.ROUNDED
        )
    
    def _get_status_display(self, status: str) -> str:
        """Get formatted status with icon and color.
        
        Args:
            status: Status string
            
        Returns:
            Formatted status string with Rich markup
        """
        status_map = {
            "planning": "[blue]🔍 Planning[/blue]",
            "executing": "[yellow]⚡ Executing[/yellow]",
            "verifying": "[magenta]🔨 Building[/magenta]",
            "waiting_reviews": "[cyan]👀 Reviews[/cyan]",
            "blocked": "[red]🚫 Blocked[/red]",
            "ready_to_merge": "[green]✅ Ready[/green]",
            "monitoring_failed": "[red]❌ Mon. Failed[/red]"
        }
        return status_map.get(status, f"[dim]{status}[/dim]")

    def _create_stats_panel(self) -> Panel:
        """Create the statistics panel with enhanced metrics."""
        table = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
        table.add_column("Metric", style="cyan bold")
        table.add_column("Value", style="white bold", justify="right")

        # Queued
        active_nums = set(self.active_issues.keys())
        queued_count = len([i for i in self.issues if i["number"] not in active_nums])
        table.add_row("📋 Queued", str(queued_count))
        
        # Active
        table.add_row("⚙️  Active", str(len(self.active_issues)))
        
        # Completed
        table.add_row("✅ Completed", f"[green]{self.stats['total_processed']}[/green]")
        
        # Failed
        if self.stats["total_failed"] > 0:
            table.add_row("❌ Failed", f"[red]{self.stats['total_failed']}[/red]")
        
        # Merged
        if self.stats["total_merged"] > 0:
            table.add_row("🚀 Auto-Merged", f"[green bold]{self.stats['total_merged']}[/green bold]")
        
        # Avg time
        if self.stats["avg_processing_time"] > 0:
            avg_min = int(self.stats["avg_processing_time"] / 60)
            avg_sec = int(self.stats["avg_processing_time"] % 60)
            table.add_row("⏱️  Avg Time", f"{avg_min}m {avg_sec}s")

        return Panel(
            table,
            title="📊 Statistics",
            border_style="yellow",
            box=box.ROUNDED
        )
    
    def _create_pr_status_panel(self) -> Panel:
        """Create the PR status panel showing review/merge status."""
        if not self.pr_statuses:
            content = Text("No PRs being monitored", style="dim italic")
            return Panel(content, title="🔍 PR Monitoring (0)", border_style="magenta", box=box.ROUNDED)
        
        table = Table(box=box.SIMPLE_HEAD, show_header=True, padding=(0, 1))
        table.add_column("PR", style="cyan bold", width=7)
        table.add_column("Reviews", style="white", width=12)
        table.add_column("Status", style="white")
        
        for pr_num, pr_data in sorted(self.pr_statuses.items(), reverse=True):
            # Review status icons
            review_status = pr_data.get("review_status", {})
            copilot = "✅" if review_status.get("copilot_complete") else "⏳"
            perplexity = "✅" if review_status.get("perplexity_complete") else (
                "⚠️" if review_status.get("perplexity_failed") else "⏳"
            )
            reviews = f"{copilot} {perplexity}"
            
            # Merge decision
            decision = pr_data.get("merge_decision", {})
            readiness = decision.get("readiness", "unknown")
            
            if readiness == "ready":
                status_str = "[green bold]✓ Ready[/green bold]"
            elif readiness == "blocked":
                blocking_count = len(decision.get("blocking_items", []))
                status_str = f"[red]🚫 Blocked ({blocking_count})[/red]"
            elif readiness == "waiting_reviews":
                status_str = "[yellow]⏳ Reviews[/yellow]"
            elif readiness == "waiting_ci":
                status_str = "[yellow]⏳ CI[/yellow]"
            elif readiness == "waiting_approval":
                status_str = "[yellow]⏳ Approval[/yellow]"
            else:
                status_str = f"[dim]{readiness}[/dim]"
            
            table.add_row(
                f"#{pr_num}",
                reviews,
                status_str
            )
        
        return Panel(
            table,
            title=f"🔍 PR Monitoring ({len(self.pr_statuses)})",
            border_style="magenta",
            box=box.ROUNDED
        )

    def _create_logs_panel(self) -> Panel:
        """Create the logs panel with colored output."""
        if not self.logs:
            content = Text("No activity yet...", style="dim italic")
            return Panel(
                content,
                title="📜 Activity Log (0)",
                border_style="dim",
                box=box.ROUNDED
            )
        
        log_text = Text()

        for log in self.logs[-10:]:  # Show last 10 logs
            # Icon based on level
            icon_map = {
                "info": "ℹ️",
                "warning": "⚠️",
                "error": "❌",
                "success": "✅"
            }
            icon = icon_map.get(log["level"], "•")
            
            style = {
                "info": "white",
                "warning": "yellow",
                "error": "red",
                "success": "green"
            }.get(log["level"], "white")

            log_text.append(f"{icon} ", style="bold")
            log_text.append(f"[{log['timestamp']}] ", style="dim")
            log_text.append(f"{log['message']}\n", style=style)

        return Panel(
            log_text,
            title=f"📜 Activity Log ({len(self.logs)})",
            border_style="white",
            box=box.ROUNDED
        )
    
    def clear_pr_status(self, pr_number: int):
        """Remove PR from monitoring display.
        
        Args:
            pr_number: Pull request number to remove
        """
        with self.lock:
            if pr_number in self.pr_statuses:
                del self.pr_statuses[pr_number]
            self._refresh()
    
    def get_stats(self) -> Dict:
        """Get current statistics.
        
        Returns:
            Dictionary of current stats
        """
        with self.lock:
            return {
                **self.stats,
                "queued": len([i for i in self.issues if i["number"] not in self.active_issues]),
                "active": len(self.active_issues),
                "monitoring": len(self.pr_statuses)
            }
