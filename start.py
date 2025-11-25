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
    print("🤖 OrchestratorAI - Autonomous Development Pipeline")
    print("=" * 60)
    
    # Check CLI availability
    print("\n[STARTUP] Checking CLI tool availability...")
    tools = check_cli_availability()
    
    print(f"\n  Claude CLI:          {'✅ Available' if tools['claude'] else '❌ Not found'}")
    print(f"  Copilot CLI:         {'✅ Available' if tools['copilot'] else '❌ Not found'}")
    print(f"  GitHub Copilot CLI:  {'✅ Available' if tools['gh_copilot'] else '❌ Not found'}")
    
    # Determine runtime configuration
    use_claude_cli = tools["claude"]
    use_copilot_cli = tools["copilot"] or tools["gh_copilot"]
    
    # Override from .env if explicitly set
    env_claude = os.getenv("USE_CLAUDE_CLI", "").lower()
    env_copilot = os.getenv("USE_COPILOT_CLI", "").lower()
    
    if env_claude == "false":
        use_claude_cli = False
        print("\n  ⚠️  Claude CLI disabled via .env (USE_CLAUDE_CLI=false)")
    if env_copilot == "false":
        use_copilot_cli = False
        print("  ⚠️  Copilot CLI disabled via .env (USE_COPILOT_CLI=false)")
    
    # Set runtime environment variables
    os.environ["USE_CLAUDE_CLI"] = "true" if use_claude_cli else "false"
    os.environ["USE_COPILOT_CLI"] = "true" if use_copilot_cli else "false"
    os.environ["USE_CLAUDE_API"] = "false"  # Always disable API unless explicitly enabled
    
    print("\n[RUNTIME CONFIG]")
    print(f"  Claude CLI:   {'✅ Enabled' if use_claude_cli else '❌ Disabled'}")
    print(f"  Copilot CLI:  {'✅ Enabled' if use_copilot_cli else '❌ Disabled'}")
    print(f"  Claude API:   ❌ Disabled (use only in emergencies)")
    
    # Warning if neither CLI is available
    if not use_claude_cli and not use_copilot_cli:
        print("\n⚠️  WARNING: No AI CLI tools available!")
        print("   The orchestrator will use fallback (simple) code generation.")
        print("   Install Claude or Copilot CLI for AI-powered generation:")
        print("   - Claude CLI: npm install -g @anthropic-ai/claude-cli")
        print("   - Copilot CLI: gh extension install github/gh-copilot")
        
        response = input("\nContinue anyway? [y/N]: ")
        if response.lower() not in ["y", "yes"]:
            print("\nExiting...")
            sys.exit(0)
    
    print("\n" + "=" * 60)
    print("Starting OrchestratorAI...\n")
    
    # Import and run the main orchestrator
    from src.main import main as orchestrator_main
    orchestrator_main()


if __name__ == "__main__":
    main()
