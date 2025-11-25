# OrchestratorAI - Quick Start Guide

## 🚀 How to Start the App

### Simple Start (Recommended)
```bash
python start.py
```

This will:
1. Check which AI agents are available (Claude CLI, Copilot CLI)
2. Auto-configure based on what's installed
3. Launch the interactive menu

### Direct Start (Advanced)
```bash
python -m src.main
```

This launches the menu directly without CLI checks.

---

## 📋 Interactive Menu

When you start the app, you'll see:

```
🤖 OrchestratorAI - Main Menu

#    Action                          Description
1    🚀 Start Orchestration          Process all AI-ready issues
2    🎯 Process Single Issue         Work on a specific issue number
3    📊 Show Dashboard               View live status dashboard
4    🔍 Monitor PR                   Monitor specific PR for reviews
5    ⚙️  Settings                    Configure AI agents and options
6    📋 List Issues                  View all AI-ready issues
7    🧪 Test Mode                    Run in dry-run mode (no changes)
0    ❌ Exit                         Quit OrchestratorAI
```

---

## ⚙️ Configuration

### AI Agents (No API Credits!)

The app uses **CLI tools by default** - no API credits consumed:

- **Claude Code CLI** (`claude`) - For planning and code generation
- **GitHub Copilot CLI** (`copilot` or `gh copilot`) - For code generation

### Install AI Agents

**Claude CLI:**
```bash
npm install -g @anthropic-ai/claude-cli
```

**GitHub Copilot CLI:**
```bash
gh extension install github/gh-copilot
```

### API Fallback (Uses Credits)

If both CLI tools fail, the app can fall back to:
1. **Simple template generation** (default, no AI)
2. **Claude API** (if enabled in settings)

To enable Claude API (not recommended unless necessary):
```bash
# In .env file
USE_CLAUDE_API=true
```

⚠️ **Warning:** Claude API consumes API credits! Use only as last resort.

---

## 🎯 Common Use Cases

### 1. Process All AI-Ready Issues
```
Select option: 1
```
- Automatically processes all issues labeled `status:ai-ready`
- Shows live dashboard
- Creates PRs for successful implementations

### 2. Work on Specific Issue
```
Select option: 2
Enter issue number: 521
```
- Processes just that one issue
- Useful for testing or debugging

### 3. Test Without Changes
```
Select option: 7
```
- Runs in dry-run mode
- Simulates all actions without making changes
- Safe for testing

### 4. Monitor PR Reviews
```
Select option: 4
Enter PR number: 522
```
- Waits for GitHub Copilot and Perplexity reviews
- Parses review comments
- Provides merge recommendation

### 5. Check AI Agent Status
```
Select option: 5
```
- Shows which AI agents are available
- Temporarily enable/disable agents
- Change settings for current session

---

## 🔧 Command Line Options (Advanced)

If you prefer command line over menu:

```bash
# Disable Claude CLI (if rate-limited)
python -m src.main --no-claude-cli

# Disable Copilot CLI
python -m src.main --no-copilot-cli

# Dry run mode
python -m src.main --dry-run

# Process specific issue
python -m src.main --issue 521

# No dashboard (logs only)
python -m src.main --no-dashboard
```

---

## 📊 Dashboard Explained

The compact dashboard shows:

### Stats Panel
- **Queue:** Issues waiting to be processed
- **Active:** Currently processing
- **Done:** Successfully completed
- **Fail:** Failed attempts
- **Merge:** Auto-merged PRs

### Active Panel
- Shows issues currently being worked on
- Status (Plan, Code, Build, Review, Ready)
- Time elapsed

### PR Status Panel
- Review completion (✓ = done, ⏳ = waiting, ⚠ = warning)
- Merge readiness (✓ = ready, 🚫 = blocked)

### Log Panel
- Recent activity (last 6 events)
- Timestamps and status messages

---

## 🛡️ Safety Features

### 1. Build Verification
Every code generation is verified with `npm run build` before PR creation.

### 2. Dry Run Mode
Test changes without affecting the repository.

### 3. No Auto-Merge by Default
PRs require manual review and merge (unless `AUTOPILOT_MODE=true`).

### 4. Worktree Isolation
Code is generated in isolated git worktrees, not your main branch.

### 5. API Credit Protection
CLI tools used by default - API only when explicitly enabled.

---

## 🐛 Troubleshooting

### "No AI agents available"
**Solution:** Install Claude CLI or Copilot CLI (see above).

### Claude CLI rate limited
**Solution:**
1. Use menu option 5 (Settings)
2. Disable Claude CLI
3. Enable Copilot CLI (or vice versa)

Or via command line:
```bash
python -m src.main --no-claude-cli
```

### "Command not found: claude"
**Solution:** Install globally:
```bash
npm install -g @anthropic-ai/claude-cli
```

### "Command not found: copilot"
**Solution:** Install via gh CLI:
```bash
gh extension install github/gh-copilot
```

### Build fails
**Solution:**
- Check the worktree location in logs
- Inspect generated code manually
- Build failures prevent PR creation (safety feature)

---

## 📁 File Structure

```
orchestratorai/
├── start.py              # Main entry point (use this!)
├── src/
│   ├── main.py           # Interactive menu system
│   ├── menu.py           # Menu UI
│   ├── orchestrator.py   # Core orchestration logic
│   ├── dashboard.py      # Live dashboard
│   ├── agents/
│   │   ├── claude.py     # Claude planning agent
│   │   └── copilot.py    # Copilot code generation
│   ├── monitoring/
│   │   ├── pr_monitor.py # PR review monitoring
│   │   └── merge_recommender.py
│   └── planning/
│       ├── review_parser.py
│       └── plan_manager.py
├── data/                 # State and generated code
└── .env                  # Configuration
```

---

## 💡 Tips

1. **Start with test mode** (option 7) to understand the flow
2. **Use single issue mode** (option 2) for debugging
3. **Check agent status** (option 5) if something fails
4. **Keep CLI tools updated** for best results
5. **Monitor the dashboard** to see real-time progress

---

## 📞 Need Help?

- Check logs in `data/` directory
- Review generated code in `data/generated_code/issue-XXX/`
- Inspect worktrees in `clarium/.worktrees/`
- Check PR comments for review feedback

---

**Happy Orchestrating! 🎉**
