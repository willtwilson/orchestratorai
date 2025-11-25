# 🎮 How to Start OrchestratorAI

## Prerequisites Checklist

Before starting, ensure you have:

- [x] Python 3.11+ installed
- [x] GitHub CLI authenticated (`gh auth login`)
- [x] `.env` file configured with API keys
- [x] Dependencies installed (`pip install -r requirements.txt`)

Optional (recommended):
- [ ] GitHub Copilot CLI (`gh extension install github/gh-copilot`)
- [ ] Claude CLI (`claude login`)

---

## Method 1: Automatic Start (Recommended)

This method checks your environment and provides helpful feedback:

```bash
python run.py
```

**What it does**:
1. ✅ Checks if `.env` exists
2. ✅ Verifies CLI tools are installed
3. ✅ Shows configuration status
4. ✅ Starts the live dashboard
5. ✅ Begins processing issues

**Example output**:
```
=== OrchestratorAI - Environment Check ===
============================================================
✅ .env file found

[*] CLI Tools:
  ✅ claude: Claude Code CLI v2.0.1
  ✅ copilot: GitHub Copilot CLI v1.0.0
  ✅ gh: GitHub CLI 2.40.1

[*] Python Dependencies:
  ✅ rich
  ✅ anthropic
  ✅ requests
  ✅ python-dotenv

============================================================
✅ Environment check complete!

>>> Starting in 2 seconds...
    Press Ctrl+C to cancel
```

---

## Method 2: Direct Start

Skip the environment check and start immediately:

```bash
python -u -m src.main
```

The `-u` flag ensures **unbuffered output** (important for real-time logs).

---

## Method 3: With CLI Arguments

### Disable Claude CLI (if rate-limited)

**Symptom**: "Rate limit reached until 2pm ET"

**Solution**:
```bash
python -m src.main --no-claude-cli
```

This will:
- ✅ Skip Claude CLI for code generation
- ✅ Use Copilot CLI instead
- ✅ Fall back to templates if needed

### Disable Copilot CLI

If Copilot isn't installed or available:

```bash
python -m src.main --no-copilot-cli
```

### Both CLIs Disabled

The orchestrator will use template-based generation:

```bash
python -m src.main --no-claude-cli --no-copilot-cli
```

**Note**: Limited to common patterns (utilities, helpers)

### Dry Run Mode

Test the orchestrator without making any changes:

```bash
python -m src.main --dry-run
```

This will:
- ✅ Fetch issues from GitHub
- ✅ Run Perplexity research
- ✅ Create implementation plans
- ✅ Simulate code generation
- ❌ NOT create worktrees
- ❌ NOT commit changes
- ❌ NOT create pull requests

**Perfect for**: Testing configuration, verifying connectivity, previewing behavior

### Process Specific Issue

Instead of processing all `status:ai-ready` issues, target a specific one:

```bash
python -m src.main --issue 521
```

**Use case**: Testing on a known issue before batch processing

### Run Without Dashboard

For logging to file or headless environments:

```bash
python -m src.main --no-dashboard
```

**Output**: Simple console logs instead of live dashboard

**Redirect to file**:
```bash
python -m src.main --no-dashboard > orchestrator.log 2>&1
```

### Combined Options

```bash
# Dry run on specific issue, no Claude CLI, no dashboard
python -m src.main --dry-run --issue 521 --no-claude-cli --no-dashboard
```

---

## Method 4: Via Python Script

Create a custom startup script:

```python
# my_orchestrator.py

from src.dashboard import Dashboard
from src.orchestrator import Orchestrator

# Start dashboard
dashboard = Dashboard()
dashboard.start()

try:
    # Start orchestrator
    orchestrator = Orchestrator(dashboard)
    
    # Option 1: Process all ready issues
    orchestrator.run()
    
    # Option 2: Process specific issue
    # issue = orchestrator.github.get_issue(521)
    # orchestrator.process_issue(issue)
    
finally:
    # Stop dashboard on exit
    dashboard.stop()
```

Run it:
```bash
python my_orchestrator.py
```

---

## Configuration via Environment Variables

Instead of CLI flags, you can set these in `.env`:

```bash
# Disable Claude CLI permanently
USE_CLAUDE_CLI=false

# Disable Copilot CLI permanently
USE_COPILOT_CLI=false

# Enable dry run mode
DRY_RUN=true
```

**CLI flags override environment variables**, so you can:

```bash
# .env has USE_CLAUDE_CLI=true
# But temporarily disable it:
python -m src.main --no-claude-cli
```

---

## What Happens When You Start?

### 1. Environment Loading
```
[DEBUG] Initializing orchestrator...
[DEBUG] Creating GitHub client...
[DEBUG] Creating Claude agent...
✅ Claude API disabled. Using CLI only (no API credits consumed).
[DEBUG] Creating Copilot agent...
[DEBUG] Creating Perplexity client...
[DEBUG] Creating build verifier...
[DEBUG] Creating PR monitoring components...
```

### 2. Dashboard Initialization
```
    ____           __              __            __            ___    ____
   / __ \___  ____/ /_  ___  _____/ /_________ _/ /_____  ____/   |  /  _/
  / / / / _ \/ __  / / / / / / / / / ___/ __ `/ __/ __ \/ __/ /| |  / /  
 / /_/ /  __/ /_/ / /_/ / /_/ / / /__/ /_/ / /_/ /_/ / / / ___ |_/ /   
 \____/\___/\__,_/\__, /\__,_/_/\___/\__,_/\__/\____/_/_/_/  |_/___/   
                 /____/                                                 

AI Development Orchestrator

📊 Live dashboard started
```

### 3. Issue Processing Loop
```
[GITHUB] Fetching issues with label: status:ai-ready
[FOUND] 3 issues ready for processing

[T+00:00] Processing issue #521: Add string utility functions
[T+00:05] [PERPLEXITY] Researching issue...
[T+00:15] [CLAUDE CLI] Creating implementation plan...
[T+00:30] [COPILOT CLI] Generating code...
[T+01:15] [BUILD] Running npm build...
[T+02:00] ✅ Build passed!
[T+02:05] [PR] Creating pull request...
[T+02:10] ✅ PR #145 created
[T+02:15] [MONITOR] Waiting for reviews...
```

### 4. Dashboard Updates (Live)
The dashboard shows real-time progress:
- Issue moves from **Queued** → **Active** → **Monitoring**
- Status updates: Planning → Executing → Building → Reviews
- Statistics increment: Completed count increases
- Activity log shows each step

---

## Stopping the Orchestrator

### Graceful Shutdown

Press `Ctrl+C` in the terminal:

```
^C
Shutting down gracefully...
📊 Dashboard stopped
```

**What happens**:
- Current issue processing completes
- Dashboard stops cleanly
- No data loss
- Worktrees preserved

### Force Stop

If it hangs, press `Ctrl+C` again:

```
^C^C
[Force quit]
```

**Cleanup needed**:
```bash
# Remove stale worktrees
git worktree prune

# Check for orphaned processes
ps aux | grep orchestrator
```

---

## Troubleshooting Startup Issues

### Error: ".env file not found"

**Solution**:
```bash
cp .env.example .env
# Edit .env with your API keys
```

### Error: "Missing required environment variables"

**Check**:
```bash
cat .env | grep -E "GITHUB_TOKEN|PERPLEXITY_API_KEY|GITHUB_REPO"
```

**Required**:
- `GITHUB_TOKEN=ghp_xxxxx`
- `GITHUB_REPO=owner/repo`
- `PERPLEXITY_API_KEY=pplx_xxxxx`
- `ANTHROPIC_API_KEY=sk-ant-xxxxx` (optional)

### Error: "gh: command not found"

**Install GitHub CLI**:
- macOS: `brew install gh`
- Windows: Download from https://cli.github.com/
- Linux: See https://github.com/cli/cli/blob/trunk/docs/install_linux.md

**Then authenticate**:
```bash
gh auth login
```

### Error: "ModuleNotFoundError: No module named 'rich'"

**Install dependencies**:
```bash
pip install -r requirements.txt
```

### Dashboard Not Displaying Correctly

**Check terminal size**:
```bash
# Terminal must be at least 80 columns wide
echo $COLUMNS  # Should be >= 80
```

**Try without dashboard**:
```bash
python -m src.main --no-dashboard
```

### Claude CLI Rate Limited

**Temporary workaround**:
```bash
python -m src.main --no-claude-cli
```

**Permanent setting** (in `.env`):
```bash
USE_CLAUDE_CLI=false
```

Rate limit resets at **2pm ET daily**.

### Copilot CLI Not Installed

**Install**:
```bash
gh extension install github/gh-copilot
```

**Or disable**:
```bash
python -m src.main --no-copilot-cli
```

---

## Verifying Successful Startup

When started successfully, you should see:

1. ✅ ASCII banner (OrchestratorAI)
2. ✅ Environment checks passing
3. ✅ "Live dashboard started" message
4. ✅ Dashboard showing queued issues
5. ✅ "CLI only (no API credits consumed)" message

**Example successful startup**:
```
    ____           __              __            __            ___    ____
   / __ \___  ____/ /_  ___  _____/ /_________ _/ /_____  ____/   |  /  _/
  [...]

AI Development Orchestrator

[DEBUG] Initializing orchestrator...
✅ Claude API disabled. Using CLI only (no API credits consumed).
[CONFIG] Claude CLI: ✅ Enabled
[CONFIG] Copilot CLI: ✅ Enabled
[CONFIG] API usage: ❌ Disabled (CLI only)

📊 Live dashboard started
Starting OrchestratorAI...

┌─────────────────────────────────────────────────┐
│ 🤖 OrchestratorAI - Autonomous Dev Pipeline    │
└─────────────────────────────────────────────────┘

[GITHUB] Fetching issues with label: status:ai-ready
[FOUND] 3 issues ready for processing
```

---

## Background/Daemon Mode

### Unix/Linux/Mac

```bash
# Start in background
nohup python -u -m src.main --no-dashboard > orchestrator.log 2>&1 &

# Check if running
ps aux | grep orchestrator

# View logs
tail -f orchestrator.log

# Stop
pkill -f "src.main"
```

### Windows (PowerShell)

```powershell
# Start in background
Start-Process python -ArgumentList "-u","-m","src.main","--no-dashboard" `
  -RedirectStandardOutput orchestrator.log `
  -RedirectStandardError error.log `
  -WindowStyle Hidden

# Check if running
Get-Process python

# View logs
Get-Content orchestrator.log -Wait

# Stop
Stop-Process -Name python
```

---

## Next Steps After Starting

1. **Monitor the dashboard** - Watch issues being processed
2. **Check GitHub** - PRs will be created automatically
3. **Review PRs** - Merge when ready
4. **Add more issues** - Label them with `status:ai-ready`
5. **Scale up** - Increase `MAX_CONCURRENT_ISSUES` in `.env`

---

## Quick Reference

| Command | Purpose |
|---------|---------|
| `python run.py` | Standard start with checks |
| `python -u -m src.main` | Direct start |
| `python -m src.main --dry-run` | Test mode |
| `python -m src.main --issue 521` | Single issue |
| `python -m src.main --no-claude-cli` | Skip Claude |
| `python -m src.main --no-dashboard` | Headless mode |
| `python -m src.main --help` | Show all options |

---

**Ready to start? Run: `python run.py`** 🚀
