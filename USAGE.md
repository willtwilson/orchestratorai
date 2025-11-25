# 📖 OrchestratorAI Usage Guide

## Table of Contents
1. [Installation](#installation)
2. [Starting the Orchestrator](#starting-the-orchestrator)
3. [CLI Options](#cli-options)
4. [Configuration](#configuration)
5. [Code Generation Strategies](#code-generation-strategies)
6. [Dashboard Guide](#dashboard-guide)
7. [Troubleshooting](#troubleshooting)

---

## Installation

### Prerequisites

1. **Python 3.11+**
2. **GitHub CLI** authenticated:
   ```bash
   gh auth login
   ```
3. **Git** configured

### Optional CLI Tools (Recommended)

**GitHub Copilot CLI**:
```bash
# Via gh extension (recommended)
gh extension install github/gh-copilot

# Or standalone
npm install -g @github/copilot-cli
```

**Claude CLI**:
```bash
# Install from https://www.anthropic.com/cli
# Then authenticate
claude login
```

### Python Dependencies

```bash
pip install -r requirements.txt
```

Required packages:
- `rich` - Terminal UI
- `anthropic` - Claude API (emergency fallback only)
- `requests` - HTTP client
- `python-dotenv` - Environment variables
- `pyfiglet` - ASCII art banners

---

## Starting the Orchestrator

### Method 1: Simple Start (Recommended)

```bash
python run.py
```

This will:
- ✅ Check environment and CLI tools
- ✅ Display configuration status
- ✅ Start the live dashboard
- ✅ Begin processing issues

### Method 2: Direct Start

```bash
python -u -m src.main
```

The `-u` flag ensures unbuffered output (important for real-time logs).

### Method 3: Custom Python Script

```python
from src.dashboard import Dashboard
from src.orchestrator import Orchestrator

dashboard = Dashboard()
dashboard.start()

orchestrator = Orchestrator(dashboard)
orchestrator.run()
```

---

## CLI Options

### Disable Claude CLI (Rate Limited)

```bash
# Via command line argument
python -m src.main --no-claude-cli

# Via environment variable (in .env)
USE_CLAUDE_CLI=false
```

### Disable Copilot CLI

```bash
# Via command line
python -m src.main --no-copilot-cli

# Via environment variable
USE_COPILOT_CLI=false
```

### Dry Run Mode

Test without making any actual changes:

```bash
python -m src.main --dry-run
```

This will:
- ✅ Fetch issues
- ✅ Run planning
- ✅ Simulate code generation
- ❌ NOT create worktrees
- ❌ NOT commit changes
- ❌ NOT create PRs

### Process Specific Issue

```bash
python -m src.main --issue 521
```

Only processes issue #521, ignoring all others.

### Run Without Dashboard

For logging to file or simple terminal:

```bash
python -m src.main --no-dashboard > output.log 2>&1
```

### Combined Options

```bash
# Dry run on specific issue, no Claude CLI
python -m src.main --dry-run --issue 521 --no-claude-cli
```

---

## Configuration

### Required Environment Variables

Create `.env` file:

```bash
# GitHub
GITHUB_TOKEN=ghp_xxxxx           # Personal access token
GITHUB_REPO=owner/repo           # Target repository
CLARIUM_PATH=/path/to/local/repo # Local path to repo

# Perplexity (for research/planning)
PERPLEXITY_API_KEY=pplx_xxxxx    # API key

# Claude API (emergency fallback only)
ANTHROPIC_API_KEY=sk-ant-xxxxx   # Optional
USE_CLAUDE_API=false             # Keep disabled to save credits
```

### CLI Tool Configuration

```bash
# Code Generation Strategy
USE_CLAUDE_CLI=true      # Enable claude CLI (no API credits)
USE_COPILOT_CLI=true     # Enable copilot CLI (no API credits)

# Fallback will use template generation if both disabled
```

### Safety Settings

```bash
DRY_RUN=false            # Set true to simulate
AUTO_MERGE=false         # Require manual PR approval
MAX_RETRIES=1            # Limit retry attempts
REQUIRE_TESTS=true       # Enforce build verification
```

### PR Management

```bash
AUTO_CREATE_PR=true              # Auto-create PRs after build
AUTO_CLEANUP_WORKTREE=false      # Keep for inspection
PR_LABELS=automated,orchestratorai
```

### PR Monitoring

```bash
PR_MONITORING_ENABLED=true
PERPLEXITY_TIMEOUT_MINUTES=10    # Max wait for Perplexity review
PR_POLL_INTERVAL_SECONDS=30      # Check interval
REQUIRE_HUMAN_APPROVAL=true      # Need human approval
REQUIRE_CI_PASS=true             # Need CI success
```

### Autopilot Mode (⚠️ Use with Caution)

```bash
AUTOPILOT_MODE=false             # Full automation
AUTO_MERGE_READY_PRS=false       # Auto-merge ready PRs
```

**Recommendation**: Keep these `false` for safety. Review PRs manually.

---

## Code Generation Strategies

The orchestrator tries code generation in this order:

### 1. GitHub Copilot CLI (Primary)

**Command**: `copilot suggest` or `gh copilot suggest`

**Enabled when**: `USE_COPILOT_CLI=true`

**Cost**: Free (CLI-based)

**Pros**:
- No API credits consumed
- Fast responses
- Integrates with GitHub ecosystem

**Cons**:
- Requires GitHub Copilot subscription
- May be rate-limited

**Disable if**:
```bash
python -m src.main --no-copilot-cli
```

### 2. Claude Code CLI (Secondary)

**Command**: `claude chat @prompt.txt`

**Enabled when**: `USE_CLAUDE_CLI=true`

**Cost**: Free (CLI-based, uses your Claude subscription)

**Pros**:
- No API credits consumed
- High-quality code generation
- Understands complex context

**Cons**:
- Rate limited (resets at 2pm ET daily)
- Requires Claude Code subscription

**Disable if rate-limited**:
```bash
python -m src.main --no-claude-cli
```

Or temporarily in `.env`:
```bash
USE_CLAUDE_CLI=false
```

### 3. Claude API (Emergency Fallback)

**Enabled when**: `USE_CLAUDE_API=true`

**Cost**: ~$0.02 per issue (API credits consumed!)

**Only use if**:
- Both CLI tools are unavailable
- You need guaranteed reliability
- You're willing to pay API costs

**Enable**:
```bash
# In .env
USE_CLAUDE_API=true
ANTHROPIC_API_KEY=sk-ant-xxxxx
```

### 4. Template Fallback (Last Resort)

**Always available**: No AI required

**How it works**: Creates basic TypeScript files from templates

**Limited to**: Common patterns (string helpers, utilities)

**Cost**: Free

This runs automatically if all AI methods fail.

---

## Dashboard Guide

The live dashboard shows:

### Header
```
🤖 OrchestratorAI - Autonomous Development Pipeline | 2025-01-15 14:30:22
```

### Queued Issues (Top Left)
```
📋 Queued Issues (3)
#521  Add string utility functions
#522  Create API endpoint
#523  Fix bug in parser
```

Issues with `status:ai-ready` label that haven't started.

### Active Issues (Bottom Left)
```
⚙️ Active Issues (1)
#     Status            Duration  Details
#521  ⚡ Executing     45s       Generating code...
```

Currently processing issues with:
- 🔍 Planning - Creating implementation plan
- ⚡ Executing - Generating code
- 🔨 Building - Running npm build
- 👀 Reviews - Waiting for PR reviews
- ✅ Ready - Ready to merge

### Statistics (Top Right)
```
📊 Statistics
📋 Queued       3
⚙️ Active       1
✅ Completed    12
❌ Failed       0
🚀 Auto-Merged  5
⏱️ Avg Time    3m 45s
```

### PR Monitoring (Middle Right)
```
🔍 PR Monitoring (2)
PR    Reviews   Status
#145  ✅ ✅     ✓ Ready
#146  ✅ ⏳     ⏳ Reviews
```

Icons:
- ✅ Complete
- ⏳ Waiting
- ⚠️ Failed/Timeout
- 🚫 Blocked

### Activity Log (Bottom)
```
📜 Activity Log (15)
✅ [14:30:15] Issue #521 code generated (copilot-cli)
🔨 [14:30:20] Running build verification...
✅ [14:30:45] Build passed!
🚀 [14:30:50] PR #145 created
```

Recent actions with timestamps and icons.

---

## Troubleshooting

### Claude CLI Rate Limited

**Symptom**: "Rate limit reached until 2pm ET"

**Solution**:
```bash
# Disable temporarily
python -m src.main --no-claude-cli

# Or in .env
USE_CLAUDE_CLI=false
```

The orchestrator will use Copilot or fallback automatically.

### Copilot CLI Not Found

**Symptom**: `copilot: command not found`

**Solutions**:

1. Install via gh extension:
   ```bash
   gh extension install github/gh-copilot
   ```

2. Or disable:
   ```bash
   USE_COPILOT_CLI=false
   ```

### Build Failures

**Symptom**: "Build failed: npm ERR!"

**Debug**:

1. Find worktree:
   ```bash
   cd C:/Users/willt/Documents/Projects/clarium
   git worktree list
   ```

2. Inspect failed build:
   ```bash
   cd .worktrees/issue-521
   npm run build
   ```

3. View generated code:
   ```bash
   cat src/utils/stringHelpers.ts
   ```

4. Check backup:
   ```bash
   ls data/generated_code/issue-521/
   ```

### Worktree Conflicts

**Symptom**: "worktree already exists"

**Solutions**:

1. List worktrees:
   ```bash
   git worktree list
   ```

2. Remove specific worktree:
   ```bash
   git worktree remove .worktrees/issue-521 --force
   ```

3. Prune stale worktrees:
   ```bash
   git worktree prune
   ```

### Dashboard Not Updating

**Symptom**: Dashboard frozen or not refreshing

**Solutions**:

1. Restart without dashboard:
   ```bash
   python -m src.main --no-dashboard
   ```

2. Check terminal size (Rich requires minimum dimensions)

3. Update Rich:
   ```bash
   pip install --upgrade rich
   ```

### API Credit Protection

**Verify no API usage**:

```bash
# Check .env
grep USE_CLAUDE_API .env
# Should show: USE_CLAUDE_API=false

# Check during runtime
# Console will show:
# ✅ Claude API disabled. Using CLI only (no API credits consumed)
# [CONFIG] API usage: ❌ Disabled (CLI only)
```

### Environment Variables Not Loading

**Symptom**: "Missing required environment variables"

**Solutions**:

1. Check .env exists:
   ```bash
   ls -la .env
   ```

2. Verify format:
   ```bash
   cat .env | grep GITHUB_TOKEN
   ```

3. No quotes needed:
   ```bash
   # ✅ Correct
   GITHUB_TOKEN=ghp_xxxxx
   
   # ❌ Wrong
   GITHUB_TOKEN="ghp_xxxxx"
   ```

### Permission Denied Errors

**Symptom**: "Permission denied" when creating worktrees

**Solution**:

Ensure CLARIUM_PATH points to a writable directory:
```bash
# In .env
CLARIUM_PATH=C:/Users/willt/Documents/Projects/clarium
```

Run with elevated permissions if needed (not recommended for regular use).

---

## Advanced Usage

### Run in Background

```bash
# Unix/Mac
nohup python -u -m src.main > orchestrator.log 2>&1 &

# Windows (PowerShell)
Start-Process python -ArgumentList "-u -m src.main" -RedirectStandardOutput orchestrator.log -RedirectStandardError error.log
```

### Schedule with Cron

```cron
# Run every hour
0 * * * * cd /path/to/orchestratorai && python -u -m src.main >> logs/cron.log 2>&1
```

### Docker Container

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "-u", "-m", "src.main", "--no-dashboard"]
```

```bash
docker build -t orchestratorai .
docker run -d --env-file .env orchestratorai
```

---

## Best Practices

1. **Start with Dry Run**: Test configuration first
   ```bash
   python -m src.main --dry-run
   ```

2. **Process Single Issues**: Test on one issue before batch
   ```bash
   python -m src.main --issue 521
   ```

3. **Monitor Dashboard**: Watch active processing in real-time

4. **Keep Worktrees**: Disable auto-cleanup for inspection
   ```bash
   AUTO_CLEANUP_WORKTREE=false
   ```

5. **Manual Approval**: Keep autopilot disabled
   ```bash
   AUTOPILOT_MODE=false
   REQUIRE_HUMAN_APPROVAL=true
   ```

6. **Regular Cleanup**: Periodically clean worktrees
   ```bash
   git worktree prune
   ```

---

## Support

- **Documentation**: See README.md and inline code comments
- **Issues**: https://github.com/willtwilson/orchestratorai/issues
- **Logs**: Check `data/` directory for detailed logs

---

**Built with ❤️ by the OrchestratorAI team**
