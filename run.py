#!/usr/bin/env python3
"""
OrchestratorAI Startup Script

This script starts the orchestrator with the live dashboard.
It checks CLI tool availability and provides helpful messages.
"""

import os
import sys
import subprocess
from pathlib import Path

# Fix Windows console encoding issues
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())


def check_cli_tool(command: str, install_hint: str = None) -> tuple[bool, str]:
    """Check if a CLI tool is available.
    
    Args:
        command: Command to check (e.g., 'claude', 'copilot')
        install_hint: Optional installation hint
        
    Returns:
        Tuple of (is_available: bool, version: str)
    """
    try:
        result = subprocess.run(
            [command, "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            version = result.stdout.strip().split('\n')[0]
            return True, version
        return False, ""
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False, ""


def check_environment():
    """Check environment and CLI tools before starting."""
    print("=== OrchestratorAI - Environment Check ===\n")
    print("="*60)
    
    # Check .env file
    env_file = Path(".env")
    if not env_file.exists():
        print("❌ .env file not found!")
        print("   Copy .env.example to .env and configure your keys")
        return False
    print("✅ .env file found")
    
    # Check CLI tools
    cli_tools = {
        "claude": {
            "env_var": "USE_CLAUDE_CLI",
            "install": "Install with: npm install -g @anthropic-ai/claude-cli"
        },
        "copilot": {
            "env_var": "USE_COPILOT_CLI", 
            "install": "Install with: gh extension install github/gh-copilot"
        },
        "gh": {
            "env_var": None,
            "install": "Install from: https://cli.github.com/"
        }
    }
    
    print("\n[*] CLI Tools:")
    all_available = True
    
    for cmd, info in cli_tools.items():
        available, version = check_cli_tool(cmd)
        env_var = info["env_var"]
        
        if available:
            print(f"  ✅ {cmd}: {version}")
        else:
            # Check if it's disabled in env
            if env_var and os.getenv(env_var, "true").lower() == "false":
                print(f"  ⏭️  {cmd}: Disabled in .env (${env_var}=false)")
            else:
                print(f"  ⚠️  {cmd}: Not found")
                print(f"      {info['install']}")
                if env_var:
                    print(f"      Or disable in .env: {env_var}=false")
                    all_available = False
    
    # Check Python packages
    print("\n[*] Python Dependencies:")
    required_packages = ['rich', 'anthropic', 'requests', 'python-dotenv']
    
    for pkg in required_packages:
        try:
            __import__(pkg.replace('-', '_'))
            print(f"  ✅ {pkg}")
        except ImportError:
            print(f"  ❌ {pkg} - Run: pip install {pkg}")
            all_available = False
    
    print("="*60)
    
    if not all_available:
        print("\n⚠️  Some dependencies are missing (see above)")
        print("   The orchestrator will use fallback methods where possible")
        
    print("\n✅ Environment check complete!")
    return True


def print_usage_help():
    """Print usage information."""
    print("\n=== Quick Start ===")
    print("   The orchestrator will process issues with the 'status:ai-ready' label")
    print("   It will use CLI tools (no API credits for code generation)")
    print("\n=== Configuration (.env) ===")
    print("   USE_CLAUDE_CLI=true/false   - Enable Claude Code CLI")
    print("   USE_COPILOT_CLI=true/false  - Enable GitHub Copilot CLI")
    print("   USE_CLAUDE_API=false        - Never use API (save credits)")
    print("   AUTOPILOT_MODE=false        - Require manual PR approval")
    print("\n>>> Starting in 2 seconds...")
    print("    Press Ctrl+C to cancel\n")


def main():
    """Main entry point."""
    # Load .env early
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        print("⚠️  python-dotenv not installed, trying without .env loading...")
    
    # Check environment
    if not check_environment():
        sys.exit(1)
    
    # Print usage help
    print_usage_help()
    
    # Give user a chance to cancel
    try:
        import time
        time.sleep(2)
    except KeyboardInterrupt:
        print("\n[!] Cancelled by user")
        sys.exit(0)
    
    # Start the orchestrator
    print("="*60)
    print("\n")
    
    try:
        from src.main import main as orchestrator_main
        orchestrator_main()
    except Exception as e:
        print(f"\n[ERROR] Error starting orchestrator: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
