# 🚀 OrchestratorAI - Quick Start Guide

## How to Start the Orchestrator

### Simple Method (Recommended)
```bash
python run.py
```

This will:
- ✅ Check your environment
- ✅ Verify CLI tools are available
- ✅ Show configuration status
- ✅ Start the live dashboard
- ✅ Begin processing issues

### Manual Method
```bash
python -m src.main
```

### Command Line Arguments
```bash
# Check environment only (don't start)
python run.py --check-only

# Force start even with warnings
python run.py --force
```

---

## 🎯 What It Does

1. **Fetches Issues** - Finds GitHub issues with `status:ai-ready` label
2. **Research** - Uses Perplexity API to research the issue
3. **Planning** - Uses Claude Code CLI to create implementation plan
4. **Code Generation** - Uses Copilot CLI to generate code
5. **Build Verification** - Runs npm build to verify code quality
6. **PR Creation** - Automatically creates pull request
7. **Review Monitoring** - Waits for Copilot and Perplexity reviews
8. **Merge Recommendation** - Analyzes reviews and recommends merge
9. **Auto-Merge** (if enabled) - Merges PR when ready

---

## 📊 Live Dashboard

The dashboard shows:

### Top Bar
- 🤖 OrchestratorAI logo and timestamp

### Left Panel
- 📋 **Queued Issues** - Next issues to process (shows 5)
- ⚙️  **Active Issues** - Currently processing with status

### Right Panel  
- 📊 **Statistics** - Counts and averages
- 🔍 **PR Monitoring** - Review status of open PRs

### Bottom Panel
- 📜 **Activity Log** - Real-time event stream (last 10)

### Status Icons
- 🔍 Planning - Researching and planning
- ⚡ Executing - Generating code
- 🔨 Building - Running build verification
- 👀 Reviews - Waiting for reviews
- ✅ Ready - Ready to merge
- 🚫 Blocked - Has blocking issues

---

## ⚙️ Configuration (.env)

### Code Generation (CLI Only - No API Credits)
```bash
USE_CLAUDE_CLI=true        # Use 'claude' command
USE_COPILOT_CLI=true       # Use 'copilot' command
USE_CLAUDE_API=false       # NEVER use API (save credits)
```

**Note:** If Claude CLI is rate-limited, set `USE_CLAUDE_CLI=false` temporarily.
The system will fall back to Copilot CLI or simple templates.

### Safety Settings
```bash
DRY_RUN=false              # Enable real operations
AUTO_MERGE=false           # Require manual approval
AUTOPILOT_MODE=false       # Full automation (DANGER)
```

### PR Management
```bash
AUTO_CREATE_PR=true        # Auto-create PRs
AUTO_CLEANUP_WORKTREE=false # Keep worktrees for inspection
PR_LABELS=automated,orchestratorai
```

### PR Monitoring
```bash
PR_MONITORING_ENABLED=true
PERPLEXITY_TIMEOUT_MINUTES=10
PR_POLL_INTERVAL_SECONDS=30
REQUIRE_HUMAN_APPROVAL=true
REQUIRE_CI_PASS=true
```

---

## 🛠️ Available CLI Commands

### Claude Code CLI
```bash
# Check version
claude --version

# Test chat (interactive)
claude chat "Hello"

# File-based prompt
claude chat @prompt.txt
```

### GitHub Copilot CLI
```bash
# Check version
copilot --version

# Get code suggestions
copilot suggest -t code "Create a TypeScript function"

# Interactive mode
copilot
```

### GitHub CLI
```bash
# Check version
gh --version

# Alternative Copilot access
gh copilot suggest
```

---

## 🔧 Troubleshooting

### Claude CLI Rate Limited
If you see "rate limited until 2pm":
```bash
# Temporarily disable Claude CLI
# Edit .env:
USE_CLAUDE_CLI=false
```
The system will use Copilot CLI instead.

### Copilot CLI Not Found
```bash
# Install GitHub Copilot extension
gh extension install github/gh-copilot

# Verify installation
copilot --version
```

### No Issues Processing
Check that issues have the `status:ai-ready` label:
```bash
gh issue list --label "status:ai-ready"
```

### Dashboard Not Showing
The dashboard is disabled during initial testing. To enable:
- Edit `src/orchestrator.py`
- Uncomment `self.dashboard.start()` in the `run()` method

---

## 📝 Example Workflow

### 1. Create Test Issue
```bash
gh issue create \
  --title "Add string utility functions" \
  --body "Create capitalize, toTitleCase, and truncate functions" \
  --label "status:ai-ready"
```

### 2. Start Orchestrator
```bash
python run.py
```

### 3. Watch Dashboard
You'll see:
- Issue moves from "Queued" → "Active"
- Status updates: Planning → Executing → Building → Reviews
- Activity log shows each step
- PR appears in "PR Monitoring" panel

### 4. Review PR
```bash
# View created PR
gh pr list --label "automated"

# View PR details
gh pr view 123
```

### 5. Manual Merge (if autopilot disabled)
```bash
gh pr merge 123 --squash
```

Or click "Merge" in GitHub UI.

---

## 🎮 Keyboard Shortcuts

While dashboard is running:
- `Ctrl+C` - Graceful shutdown
- `Ctrl+Z` - Force quit (not recommended)

---

## 📈 Monitoring

### Check Logs
```bash
# Real-time logs are in the dashboard
# Historical logs:
tail -f orchestrator.log
```

### Check State
```bash
# View current state
cat data/state.json
```

### Check Worktrees
```bash
cd C:/Users/willt/Documents/Projects/clarium
git worktree list
```

---

## 🚨 Emergency Stop

If something goes wrong:
```bash
# 1. Stop the orchestrator
Ctrl+C

# 2. Clean up worktrees
cd C:/Users/willt/Documents/Projects/clarium
git worktree prune

# 3. Check for stuck processes
# Windows:
tasklist | findstr python
```

---

## 💡 Tips

1. **Start Small** - Process 1 issue first (`MAX_CONCURRENT_ISSUES=1`)
2. **Use Dry Run** - Test without changes (`DRY_RUN=true`)
3. **Keep Autopilot Off** - Review PRs manually until confident
4. **Monitor Credits** - Perplexity API is the only billable service
5. **Save Worktrees** - Keep `AUTO_CLEANUP_WORKTREE=false` for debugging

---

## 📞 Support

If you encounter issues:
1. Check the Activity Log in the dashboard
2. Review `data/state.json` for stuck issues
3. Check `orchestrator.log` for detailed errors
4. Verify `.env` configuration
5. Test CLI tools individually

---

**Ready to go?** Run `python run.py` and watch the magic happen! ✨
