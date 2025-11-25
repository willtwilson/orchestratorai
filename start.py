#!/usr/bin/env python3
"""
OrchestratorAI - Autonomous Development Pipeline
Start script with runtime CLI selection
"""

import os
import sys
from pathlib import Path


def check_cli_availability():
    """Check which CLI tools are available."""
    import subprocess
    
    tools = {
        "claude": False,
        "copilot": False,
        "gh_copilot": False
    }
    
    # Check 'claude' CLI
    try:
        result = subprocess.run(
            ["claude", "--version"],
            capture_output=True,
            timeout=5
        )
        tools["claude"] = result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    
    # Check 'copilot' CLI
    try:
        result = subprocess.run(
            ["copilot", "--version"],
            capture_output=True,
            timeout=5
        )
        tools["copilot"] = result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    
    # Check 'gh copilot' CLI
    try:
        result = subprocess.run(
            ["gh", "copilot", "--version"],
            capture_output=True,
            timeout=5
        )
        tools["gh_copilot"] = result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    
    return tools


def main():
    """Main entry point with CLI detection."""
    # Import rich for better formatting
    from rich.console import Console
    console = Console()
    
    console.print("\n[bold cyan]🤖 OrchestratorAI - Interactive Mode[/bold cyan]")
    console.print("=" * 60)
    
    # Check CLI availability
    console.print("\n[yellow][STARTUP] Checking AI agent availability...[/yellow]")
    tools = check_cli_availability()
    
    console.print(f"\n  Claude CLI:          {'[green]✅ Available[/green]' if tools['claude'] else '[red]❌ Not found[/red]'}")
    console.print(f"  Copilot CLI:         {'[green]✅ Available[/green]' if tools['copilot'] else '[red]❌ Not found[/red]'}")
    console.print(f"  GitHub Copilot CLI:  {'[green]✅ Available[/green]' if tools['gh_copilot'] else '[red]❌ Not found[/red]'}")
    
    # Determine runtime configuration
    use_claude_cli = tools["claude"]
    use_copilot_cli = tools["copilot"] or tools["gh_copilot"]
    
    # Override from .env if explicitly set
    env_claude = os.getenv("USE_CLAUDE_CLI", "").lower()
    env_copilot = os.getenv("USE_COPILOT_CLI", "").lower()
    
    if env_claude == "false":
        use_claude_cli = False
        console.print("\n  [yellow]⚠️  Claude CLI disabled via .env (USE_CLAUDE_CLI=false)[/yellow]")
    if env_copilot == "false":
        use_copilot_cli = False
        console.print("  [yellow]⚠️  Copilot CLI disabled via .env (USE_COPILOT_CLI=false)[/yellow]")
    
    # Set runtime environment variables
    os.environ["USE_CLAUDE_CLI"] = "true" if use_claude_cli else "false"
    os.environ["USE_COPILOT_CLI"] = "true" if use_copilot_cli else "false"
    os.environ["USE_CLAUDE_API"] = os.getenv("USE_CLAUDE_API", "false")  # Respect .env setting
    
    console.print("\n[cyan][RUNTIME CONFIG][/cyan]")
    console.print(f"  Claude CLI:   {'[green]✅ Enabled[/green]' if use_claude_cli else '[red]❌ Disabled[/red]'}")
    console.print(f"  Copilot CLI:  {'[green]✅ Enabled[/green]' if use_copilot_cli else '[red]❌ Disabled[/red]'}")
    
    api_enabled = os.getenv("USE_CLAUDE_API", "false").lower() == "true"
    if api_enabled:
        console.print(f"  Claude API:   [red]⚠️  Enabled (uses API credits!)[/red]")
    else:
        console.print(f"  Claude API:   [green]❌ Disabled (no API credits consumed)[/green]")
    
    # Warning if neither CLI is available
    if not use_claude_cli and not use_copilot_cli and not api_enabled:
        console.print("\n[red]⚠️  WARNING: No AI agents available![/red]")
        console.print("   [yellow]The orchestrator will use fallback (simple template) generation.[/yellow]")
        console.print("   [yellow]Install an AI agent for better code generation:[/yellow]")
        console.print("     • [cyan]Claude CLI:[/cyan] npm install -g @anthropic-ai/claude-cli")
        console.print("     • [cyan]Copilot CLI:[/cyan] gh extension install github/gh-copilot")
        console.print("     • [cyan]Or enable Claude API[/cyan] in settings (uses API credits)")
        
        from rich.prompt import Confirm
        if not Confirm.ask("\n[yellow]Continue with simple template generation?[/yellow]", default=False):
            console.print("\n[dim]Exiting...[/dim]")
            sys.exit(0)
    
    console.print("\n" + "=" * 60)
    console.print("[green]Launching interactive menu...[/green]\n")
    
    # Import and run the main orchestrator
    from src.main import main as orchestrator_main
    orchestrator_main()


if __name__ == "__main__":
    main()
