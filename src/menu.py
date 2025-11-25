"""Interactive menu system for OrchestratorAI."""

import os
import sys
from typing import Optional, Callable
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box
from rich.prompt import Prompt, Confirm
from rich.text import Text


console = Console()


class Menu:
    """Interactive menu system."""

    def __init__(self):
        """Initialize the menu system."""
        self.console = Console()

    def show_main_menu(self) -> Optional[str]:
        """Display main menu and get user selection.
        
        Returns:
            Selected command or None to exit
        """
        while True:
            self._clear_screen()
            self._print_header()
            
            # Create menu table
            table = Table(
                title="🤖 OrchestratorAI - Main Menu",
                box=box.ROUNDED,
                show_header=True,
                header_style="bold cyan"
            )
            table.add_column("#", style="cyan bold", width=4)
            table.add_column("Action", style="white bold")
            table.add_column("Description", style="dim")
            
            # Menu options
            options = [
                ("1", "🚀 Start Orchestration", "Process all AI-ready issues"),
                ("2", "🎯 Process Single Issue", "Work on a specific issue number"),
                ("3", "📊 Show Dashboard", "View live status dashboard"),
                ("4", "🔍 Monitor PR", "Monitor specific PR for reviews"),
                ("5", "⚙️  Settings", "Configure AI agents and options"),
                ("6", "📋 List Issues", "View all AI-ready issues"),
                ("7", "🧪 Test Mode", "Run in dry-run mode (no changes)"),
                ("0", "❌ Exit", "Quit OrchestratorAI"),
            ]
            
            for num, action, desc in options:
                table.add_row(num, action, desc)
            
            self.console.print()
            self.console.print(table)
            self.console.print()
            
            # Get user choice
            choice = Prompt.ask(
                "[cyan]Select an option[/cyan]",
                choices=["0", "1", "2", "3", "4", "5", "6", "7"],
                default="1"
            )
            
            if choice == "0":
                self.console.print("\n[yellow]👋 Goodbye![/yellow]")
                return None
            elif choice == "1":
                return "orchestrate"
            elif choice == "2":
                return "single_issue"
            elif choice == "3":
                return "dashboard"
            elif choice == "4":
                return "monitor_pr"
            elif choice == "5":
                return "settings"
            elif choice == "6":
                return "list_issues"
            elif choice == "7":
                return "test_mode"

    def get_issue_number(self) -> Optional[int]:
        """Get issue number from user.
        
        Returns:
            Issue number or None
        """
        self.console.print("\n[cyan]Process Single Issue[/cyan]")
        issue_str = Prompt.ask("Enter issue number", default="")
        
        if not issue_str:
            return None
        
        try:
            return int(issue_str)
        except ValueError:
            self.console.print(f"[red]Invalid issue number: {issue_str}[/red]")
            return None

    def get_pr_number(self) -> Optional[int]:
        """Get PR number from user.
        
        Returns:
            PR number or None
        """
        self.console.print("\n[cyan]Monitor Pull Request[/cyan]")
        pr_str = Prompt.ask("Enter PR number", default="")
        
        if not pr_str:
            return None
        
        try:
            return int(pr_str)
        except ValueError:
            self.console.print(f"[red]Invalid PR number: {pr_str}[/red]")
            return None

    def show_settings_menu(self) -> dict:
        """Show settings configuration menu.
        
        Returns:
            Dictionary of settings to override
        """
        self._clear_screen()
        self.console.print("\n[bold cyan]⚙️  Configuration Settings[/bold cyan]\n")
        
        # Current settings
        settings_table = Table(box=box.SIMPLE, show_header=True)
        settings_table.add_column("Setting", style="cyan")
        settings_table.add_column("Current Value", style="yellow")
        settings_table.add_column("Status", style="white")
        
        use_claude_cli = os.getenv("USE_CLAUDE_CLI", "true").lower() == "true"
        use_copilot_cli = os.getenv("USE_COPILOT_CLI", "true").lower() == "true"
        use_claude_api = os.getenv("USE_CLAUDE_API", "false").lower() == "true"
        dry_run = os.getenv("DRY_RUN", "false").lower() == "true"
        autopilot = os.getenv("AUTOPILOT_MODE", "false").lower() == "true"
        
        settings_table.add_row(
            "Claude CLI",
            "Enabled" if use_claude_cli else "Disabled",
            "✅ No API credits" if use_claude_cli else "⚠️  Disabled"
        )
        settings_table.add_row(
            "Copilot CLI",
            "Enabled" if use_copilot_cli else "Disabled",
            "✅ No API credits" if use_copilot_cli else "⚠️  Disabled"
        )
        settings_table.add_row(
            "Claude API",
            "Enabled" if use_claude_api else "Disabled",
            "⚠️  Uses API credits!" if use_claude_api else "✅ Disabled"
        )
        settings_table.add_row(
            "Dry Run",
            "Enabled" if dry_run else "Disabled",
            "🔒 Safe" if dry_run else "⚡ Live"
        )
        settings_table.add_row(
            "Autopilot",
            "Enabled" if autopilot else "Disabled",
            "🤖 Auto-merge" if autopilot else "👤 Manual"
        )
        
        self.console.print(settings_table)
        self.console.print()
        
        # Offer to change settings
        overrides = {}
        
        if Confirm.ask("[cyan]Change Claude CLI?[/cyan]", default=not use_claude_cli):
            overrides["USE_CLAUDE_CLI"] = "false" if use_claude_cli else "true"
        
        if Confirm.ask("[cyan]Change Copilot CLI?[/cyan]", default=not use_copilot_cli):
            overrides["USE_COPILOT_CLI"] = "false" if use_copilot_cli else "true"
        
        if Confirm.ask("[cyan]Change Claude API? (WARNING: Uses API credits)[/cyan]", default=False):
            overrides["USE_CLAUDE_API"] = "false" if use_claude_api else "true"
        
        if Confirm.ask("[cyan]Change Dry Run mode?[/cyan]", default=False):
            overrides["DRY_RUN"] = "false" if dry_run else "true"
        
        if Confirm.ask("[cyan]Change Autopilot mode?[/cyan]", default=False):
            overrides["AUTOPILOT_MODE"] = "false" if autopilot else "true"
        
        if overrides:
            self.console.print("\n[green]✅ Settings updated for this session[/green]")
            self.console.print("[dim]Note: Changes are temporary. Update .env to persist.[/dim]\n")
            input("Press Enter to continue...")
        
        return overrides

    def confirm_action(self, message: str, default: bool = False) -> bool:
        """Ask for user confirmation.
        
        Args:
            message: Confirmation message
            default: Default choice
            
        Returns:
            True if confirmed, False otherwise
        """
        return Confirm.ask(f"[yellow]{message}[/yellow]", default=default)

    def show_agent_status(self):
        """Display AI agent availability status."""
        self.console.print("\n[bold cyan]🤖 AI Agent Status[/bold cyan]\n")
        
        status_table = Table(box=box.ROUNDED, show_header=True)
        status_table.add_column("Agent", style="cyan bold")
        status_table.add_column("Status", style="white")
        status_table.add_column("Method", style="dim")
        
        # Check Claude CLI
        claude_cli_status = self._check_command_available("claude")
        status_table.add_row(
            "Claude Code CLI",
            "✅ Available" if claude_cli_status else "❌ Not found",
            "CLI (no API credits)" if claude_cli_status else "Install: npm i -g @anthropic-ai/claude-cli"
        )
        
        # Check Copilot CLI
        copilot_status = self._check_command_available("copilot") or self._check_command_available("gh copilot")
        status_table.add_row(
            "GitHub Copilot CLI",
            "✅ Available" if copilot_status else "❌ Not found",
            "CLI (no API credits)" if copilot_status else "Install: gh extension install github/gh-copilot"
        )
        
        # Check Claude API (always available if key is set)
        has_api_key = bool(os.getenv("ANTHROPIC_API_KEY"))
        status_table.add_row(
            "Claude API (Fallback)",
            "✅ Available" if has_api_key else "❌ No API key",
            "⚠️  Uses API credits!" if has_api_key else "Set ANTHROPIC_API_KEY in .env"
        )
        
        self.console.print(status_table)
        self.console.print()
        
        # Warning if both CLIs are unavailable
        if not claude_cli_status and not copilot_status:
            self.console.print("[red]⚠️  WARNING: No CLI agents available![/red]")
            self.console.print("[yellow]Install at least one to avoid using API credits:[/yellow]")
            self.console.print("  • Claude CLI: npm install -g @anthropic-ai/claude-cli")
            self.console.print("  • Copilot CLI: gh extension install github/gh-copilot")
            self.console.print()

    def _check_command_available(self, command: str) -> bool:
        """Check if a command is available.
        
        Args:
            command: Command to check (can include spaces)
            
        Returns:
            True if available, False otherwise
        """
        import subprocess
        
        # Split command into parts
        parts = command.split()
        
        try:
            result = subprocess.run(
                parts + ["--version"],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def _clear_screen(self):
        """Clear the terminal screen."""
        os.system('cls' if os.name == 'nt' else 'clear')

    def _print_header(self):
        """Print application header."""
        import pyfiglet
        banner = pyfiglet.figlet_format("OrchestratorAI", font="slant")
        self.console.print(f"[cyan]{banner}[/cyan]")
        self.console.print("[dim]AI Development Orchestrator v1.0[/dim]\n")

    def pause(self, message: str = "Press Enter to continue..."):
        """Pause and wait for user input.
        
        Args:
            message: Message to display
        """
        input(f"\n{message}")
