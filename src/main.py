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
    
    print_banner()
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

    try:
        # Start dashboard unless disabled
        if not args.no_dashboard:
            dashboard = Dashboard()
            dashboard.start()
            console.print("[green]📊 Live dashboard started[/green]")
        else:
            dashboard = None
            console.print("[yellow]📝 Running without dashboard[/yellow]")
        
        orchestrator = Orchestrator(dashboard)

        if args.issue:
            # Process specific issue
            console.print(f"\n[cyan]🎯 Processing specific issue #{args.issue}[/cyan]")
            issue = orchestrator.github.get_issue(args.issue)
            orchestrator.process_issue(issue)
        else:
            # Normal operation
            console.print("[green]Starting OrchestratorAI...[/green]\n")
            orchestrator.run()
        
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


if __name__ == "__main__":
    main()
