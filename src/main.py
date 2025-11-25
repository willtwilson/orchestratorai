"""Main entry point for OrchestratorAI."""

import os
import sys
import argparse
from pathlib import Path
from dotenv import load_dotenv
import pyfiglet
from rich.console import Console

from .orchestrator import Orchestrator
from .dashboard import Dashboard
from .menu import Menu


console = Console()


def load_environment():
    """Load environment variables from .env file."""
    env_path = Path(__file__).parent.parent / ".env"
    if not env_path.exists():
        console.print("[red]Error: .env file not found![/red]")
        console.print("Please copy .env.example to .env and configure your API keys.")
        sys.exit(1)

    load_dotenv(env_path)

    required_vars = [
        "GITHUB_TOKEN",
        "GITHUB_REPO",
        "ANTHROPIC_API_KEY",
        "PERPLEXITY_API_KEY",
    ]

    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        console.print(f"[red]Error: Missing required environment variables:[/red]")
        for var in missing_vars:
            console.print(f"  - {var}")
        sys.exit(1)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='OrchestratorAI - Autonomous Development Pipeline',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python -m src.main                      # Normal mode
  python -m src.main --no-claude-cli      # Disable Claude CLI (if rate-limited)
  python -m src.main --no-copilot-cli     # Disable Copilot CLI
  python -m src.main --dry-run            # Simulate without changes
  python -m src.main --no-dashboard       # Run without live dashboard
  python -m src.main --issue 521          # Process specific issue only
        '''
    )
    
    parser.add_argument(
        '--no-claude-cli',
        action='store_true',
        help='Disable Claude Code CLI (useful if rate-limited)'
    )
    
    parser.add_argument(
        '--no-copilot-cli',
        action='store_true',
        help='Disable GitHub Copilot CLI'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Simulate operations without making changes'
    )
    
    parser.add_argument(
        '--no-dashboard',
        action='store_true',
        help='Run without live dashboard (simple logs only)'
    )
    
    parser.add_argument(
        '--issue',
        type=int,
        help='Process a specific issue number only'
    )
    
    return parser.parse_args()


def print_banner():
    """Print application banner."""
    banner = pyfiglet.figlet_format("OrchestratorAI", font="slant")
    console.print(f"[cyan]{banner}[/cyan]")
    console.print("[dim]AI Development Orchestrator[/dim]\n")


def main():
    """Main application entry point."""
    args = parse_args()
    
    load_environment()
    
    # Override environment variables from CLI args
    if args.no_claude_cli:
        os.environ['USE_CLAUDE_CLI'] = 'false'
        console.print("[yellow]🔧 Claude CLI disabled via command line[/yellow]")
    
    if args.no_copilot_cli:
        os.environ['USE_COPILOT_CLI'] = 'false'
        console.print("[yellow]🔧 Copilot CLI disabled via command line[/yellow]")
    
    if args.dry_run:
        os.environ['DRY_RUN'] = 'true'
        console.print("[yellow]🔒 Dry run mode enabled via command line[/yellow]")

    # Create menu system
    menu = Menu()
    
    try:
        # If command line args specify direct action, skip menu
        if args.issue or args.no_dashboard:
            # Direct command mode (legacy behavior)
            dashboard = None if args.no_dashboard else Dashboard()
            if dashboard:
                dashboard.start()
            
            orchestrator = Orchestrator(dashboard)
            
            if args.issue:
                console.print(f"\n[cyan]🎯 Processing specific issue #{args.issue}[/cyan]")
                issue = orchestrator.github.get_issue(args.issue)
                orchestrator.process_issue(issue)
            else:
                orchestrator.run()
            
            if dashboard:
                dashboard.stop()
            return

        # Interactive menu mode
        while True:
            # Show agent status on first run
            menu.show_agent_status()
            
            # Get user choice
            command = menu.show_main_menu()
            
            if command is None:
                # User chose to exit
                break
            
            # Handle settings change
            if command == "settings":
                settings_overrides = menu.show_settings_menu()
                for key, value in settings_overrides.items():
                    os.environ[key] = value
                continue
            
            # Handle list issues
            if command == "list_issues":
                _list_issues()
                menu.pause()
                continue
            
            # Handle test mode
            if command == "test_mode":
                os.environ['DRY_RUN'] = 'true'
                console.print("\n[yellow]🔒 Dry run mode enabled[/yellow]\n")
                command = "orchestrate"  # Fall through to orchestrate
            
            # Handle single issue
            issue_number = None
            if command == "single_issue":
                issue_number = menu.get_issue_number()
                if issue_number is None:
                    continue
            
            # Handle PR monitoring
            if command == "monitor_pr":
                pr_number = menu.get_pr_number()
                if pr_number is None:
                    continue
                _monitor_pr(pr_number)
                menu.pause()
                continue
            
            # Determine if dashboard should be shown
            use_dashboard = (command == "dashboard") or (command == "orchestrate")
            
            # Initialize components
            dashboard = Dashboard() if use_dashboard else None
            if dashboard:
                dashboard.start()
            
            orchestrator = Orchestrator(dashboard)
            
            try:
                if command == "dashboard":
                    # Just show dashboard, don't process
                    console.print("\n[green]📊 Dashboard active. Press Ctrl+C to return to menu.[/green]\n")
                    import time
                    while True:
                        time.sleep(1)
                
                elif command == "orchestrate":
                    # Full orchestration
                    console.print("\n[green]🚀 Starting orchestration...[/green]\n")
                    orchestrator.run()
                    console.print("\n[green]✅ Orchestration complete![/green]")
                    menu.pause()
                
                elif issue_number:
                    # Process single issue
                    console.print(f"\n[cyan]🎯 Processing issue #{issue_number}[/cyan]\n")
                    issue = orchestrator.github.get_issue(issue_number)
                    orchestrator.process_issue(issue)
                    console.print("\n[green]✅ Issue processing complete![/green]")
                    menu.pause()
            
            except KeyboardInterrupt:
                console.print("\n[yellow]Returning to menu...[/yellow]")
            
            finally:
                if dashboard:
                    dashboard.stop()

    except KeyboardInterrupt:
        console.print("\n[yellow]Shutting down gracefully...[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[red]Fatal error: {e}[/red]")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def _list_issues():
    """List all AI-ready issues."""
    from .github_client import GitHubClient
    
    console.print("\n[bold cyan]📋 AI-Ready Issues[/bold cyan]\n")
    
    github = GitHubClient(
        token=os.getenv("GITHUB_TOKEN"),
        repo=os.getenv("GITHUB_REPO")
    )
    
    issues = github.get_ai_ready_issues()
    
    if not issues:
        console.print("[yellow]No AI-ready issues found.[/yellow]")
        console.print("[dim]Add the 'status:ai-ready' label to issues to process them.[/dim]")
        return
    
    from rich.table import Table
    from rich import box
    
    table = Table(box=box.ROUNDED, show_header=True)
    table.add_column("#", style="cyan bold", width=6)
    table.add_column("Title", style="white")
    table.add_column("Labels", style="yellow", width=30)
    
    for issue in issues:
        labels = ", ".join([label["name"] for label in issue.get("labels", [])])
        table.add_row(
            f"#{issue['number']}",
            issue['title'][:50] + ("..." if len(issue['title']) > 50 else ""),
            labels[:27] + ("..." if len(labels) > 27 else "")
        )
    
    console.print(table)
    console.print(f"\n[green]Total: {len(issues)} issues[/green]")


def _monitor_pr(pr_number: int):
    """Monitor a specific PR for reviews."""
    from .monitoring.pr_monitor import PRMonitor
    from .planning.review_parser import ReviewParser
    from .planning.plan_manager import PlanManager
    from .monitoring.merge_recommender import MergeRecommender
    
    console.print(f"\n[cyan]🔍 Monitoring PR #{pr_number}...[/cyan]\n")
    
    # Initialize components
    monitor = PRMonitor(
        github_token=os.getenv("GITHUB_TOKEN"),
        repo=os.getenv("GITHUB_REPO")
    )
    
    parser = ReviewParser()
    plan_manager = PlanManager(
        github_token=os.getenv("GITHUB_TOKEN"),
        repo=os.getenv("GITHUB_REPO")
    )
    recommender = MergeRecommender()
    
    # Monitor PR
    console.print("[yellow]Waiting for reviews...[/yellow]")
    result = monitor.wait_for_reviews(pr_number, timeout=300)
    
    if not result["complete"]:
        console.print(f"[red]❌ Monitoring failed or timed out[/red]")
        console.print(f"[dim]Reason: {result.get('error', 'Unknown')}[/dim]")
        return
    
    console.print("[green]✅ Reviews complete![/green]\n")
    
    # Parse reviews
    reviews = result.get("reviews", [])
    parsed_items = parser.parse_reviews(reviews)
    
    console.print(f"[cyan]Found {len(parsed_items)} review items[/cyan]")
    
    # Create remediation plan
    plan = plan_manager.create_plan(parsed_items, pr_number)
    
    # Get merge recommendation
    recommendation = recommender.recommend_merge(plan, result)
    
    # Display recommendation
    from rich.panel import Panel
    
    if recommendation["ready_to_merge"]:
        panel = Panel(
            "[green bold]✅ READY TO MERGE[/green bold]\n\n"
            f"Confidence: {recommendation['confidence']}%\n"
            f"Reason: {recommendation['reason']}",
            title="Merge Recommendation",
            border_style="green"
        )
    else:
        blocking = recommendation.get("blocking_issues", [])
        blocking_text = "\n".join([f"  • {item}" for item in blocking[:5]])
        
        panel = Panel(
            "[red bold]❌ NOT READY[/red bold]\n\n"
            f"Blocking issues: {len(blocking)}\n\n"
            f"{blocking_text}",
            title="Merge Recommendation",
            border_style="red"
        )
    
    console.print(panel)


if __name__ == "__main__":
    main()
