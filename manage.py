#!/usr/bin/env python3
"""
OrchestratorAI Management CLI

Utility commands for managing the orchestrator.
"""

import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime


def show_status():
    """Show current orchestrator status."""
    print("=== OrchestratorAI Status ===\n")
    print("="*60)
    
    # Check state file
    state_file = Path("data/state.json")
    if state_file.exists():
        with open(state_file) as f:
            state = json.load(f)
        
        print(f"✅ State file: {state_file}")
        print(f"   Processed issues: {len(state.get('processed_issues', []))}")
        print(f"   Active issues: {len(state.get('active_issues', {}))}")
        print(f"   Completed issues: {len(state.get('completed_issues', {}))}")
        
        if state.get('active_issues'):
            print("\n📋 Active Issues:")
            for issue_num, data in state['active_issues'].items():
                status = data.get('status', 'unknown')
                started = data.get('started_at', 'unknown')
                print(f"   #{issue_num}: {status} (started: {started})")
    else:
        print("⚠️  No state file found (orchestrator hasn't run yet)")
    
    # Check worktrees
    print("\n[*] Worktrees:")
    clarium_path = Path("C:/Users/willt/Documents/Projects/clarium")
    worktree_dir = clarium_path / ".worktrees"
    
    if worktree_dir.exists():
        worktrees = list(worktree_dir.iterdir())
        if worktrees:
            for wt in worktrees:
                print(f"   {wt.name}")
        else:
            print("   (none)")
    else:
        print("   (none)")
    
    # Check for generated code backups
    print("\n[*] Code Backups:")
    backup_dir = Path("data/generated_code")
    if backup_dir.exists():
        backups = list(backup_dir.iterdir())
        if backups:
            for backup in backups:
                print(f"   {backup.name}")
        else:
            print("   (none)")
    else:
        print("   (none)")
    
    print("="*60)


def reset_state():
    """Reset orchestrator state (for testing)."""
    state_file = Path("data/state.json")
    
    if state_file.exists():
        # Backup current state
        backup_file = Path(f"data/state.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        state_file.rename(backup_file)
        print(f"✅ Backed up state to: {backup_file}")
    
    # Create fresh state
    fresh_state = {
        "processed_issues": [],
        "active_issues": {},
        "completed_issues": {}
    }
    
    state_file.parent.mkdir(exist_ok=True)
    with open(state_file, 'w') as f:
        json.dump(fresh_state, f, indent=2)
    
    print("✅ State reset to fresh")
    print("   The orchestrator will now process all issues with 'status:ai-ready'")


def cleanup_worktrees():
    """Clean up all worktrees."""
    clarium_path = Path("C:/Users/willt/Documents/Projects/clarium")
    
    print("[*] Cleaning up worktrees...")
    
    # Prune stale worktrees
    subprocess.run(
        ["git", "worktree", "prune"],
        cwd=str(clarium_path),
        capture_output=True
    )
    
    # Remove worktree directory
    worktree_dir = clarium_path / ".worktrees"
    if worktree_dir.exists():
        import shutil
        shutil.rmtree(worktree_dir, ignore_errors=True)
        print(f"✅ Removed: {worktree_dir}")
    
    print("✅ Worktrees cleaned up")


def check_env():
    """Check environment configuration."""
    print("=== Environment Configuration ===\n")
    print("="*60)
    
    env_file = Path(".env")
    if not env_file.exists():
        print("❌ .env file not found!")
        return
    
    # Read .env and show key settings
    with open(env_file) as f:
        lines = f.readlines()
    
    important_vars = {
        "USE_CLAUDE_CLI": "Claude Code CLI",
        "USE_COPILOT_CLI": "GitHub Copilot CLI",
        "USE_CLAUDE_API": "Claude API (costs credits)",
        "AUTOPILOT_MODE": "Auto-merge PRs",
        "PR_MONITORING_ENABLED": "PR monitoring",
        "REQUIRE_HUMAN_APPROVAL": "Human approval required",
        "DRY_RUN": "Dry run mode (safe)",
        "MAX_CONCURRENT_ISSUES": "Concurrent issues"
    }
    
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        
        for var, description in important_vars.items():
            if line.startswith(f"{var}="):
                value = line.split('=', 1)[1]
                icon = "[X]" if value.lower() in ('true', '1') else "[ ]"
                print(f"{icon} {description:<30} = {value}")
    
    print("="*60)


def list_issues():
    """List issues ready for processing."""
    print("=== Issues with 'status:ai-ready' label ===\n")
    
    result = subprocess.run(
        ["gh", "issue", "list", "--label", "status:ai-ready", "--json", "number,title,state"],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print("❌ Failed to fetch issues")
        print(result.stderr)
        return
    
    try:
        issues = json.loads(result.stdout)
        if not issues:
            print("No issues found with 'status:ai-ready' label")
            return
        
        for issue in issues:
            print(f"  #{issue['number']}: {issue['title']}")
            print(f"    State: {issue['state']}\n")
        
        print(f"Total: {len(issues)} issues")
    except json.JSONDecodeError:
        print("❌ Failed to parse issue list")


def show_help():
    """Show help message."""
    print("""
=== OrchestratorAI Management CLI ===

Usage: python manage.py <command>

Commands:
    status      Show current orchestrator status
    reset       Reset state (start fresh)
    cleanup     Clean up worktrees
    env         Show environment configuration
    issues      List issues ready for processing
    help        Show this help message

Examples:
    python manage.py status
    python manage.py reset
    python manage.py cleanup
    python manage.py env
    python manage.py issues
""")


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        show_help()
        return
    
    command = sys.argv[1].lower()
    
    commands = {
        'status': show_status,
        'reset': reset_state,
        'cleanup': cleanup_worktrees,
        'env': check_env,
        'issues': list_issues,
        'help': show_help
    }
    
    if command in commands:
        commands[command]()
    else:
        print(f"❌ Unknown command: {command}")
        print("Run 'python manage.py help' for usage")


if __name__ == "__main__":
    main()
