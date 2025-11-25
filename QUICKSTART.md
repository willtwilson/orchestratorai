# 🚀 Quick Start Guide

## Get Started in 5 Minutes

### 1. Clone the Repository
```bash
git clone https://github.com/willtwilson/orchestratorai.git
cd orchestratorai
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment
```bash
cp .env.example .env
```

Edit `.env` and add your API keys:
```bash
GITHUB_TOKEN=ghp_xxxxx           # Your GitHub PAT
GITHUB_REPO=owner/repo           # Target repo
PERPLEXITY_API_KEY=pplx_xxxxx    # Perplexity API key
CLARIUM_PATH=/path/to/local/repo # Local repo path
```

### 4. Install CLI Tools (Recommended)

**GitHub CLI** (required):
```bash
gh auth login
```

**GitHub Copilot CLI** (recommended):
```bash
gh extension install github/gh-copilot
```

**Claude CLI** (optional):
```bash
# Download from https://www.anthropic.com/cli
claude login
```

### 5. Run the Orchestrator

**Simple start**:
```bash
python run.py
```

**Direct start**:
```bash
python -u -m src.main
```

**With options**:
```bash
# Disable Claude if rate-limited
python -m src.main --no-claude-cli

# Dry run (no changes)
python -m src.main --dry-run

# Process specific issue
python -m src.main --issue 521
```

## What Happens Next?

1. **Dashboard starts** - Live terminal UI appears
2. **Issues detected** - Finds issues with `status:ai-ready` label
3. **Planning** - Perplexity researches, Claude plans
4. **Code generation** - Copilot/Claude CLI generates code
5. **Build verification** - Runs `npm build` to verify
6. **PR creation** - Creates pull request automatically
7. **Review monitoring** - Waits for Copilot/Perplexity reviews
8. **Merge recommendation** - Suggests when ready to merge

## Dashboard Overview

```
┌─────────────────────────────────────────────────┐
│ 🤖 OrchestratorAI - Autonomous Dev Pipeline    │
└─────────────────────────────────────────────────┘

┌─ Queued Issues ─┐  ┌─ Statistics ─────┐
│ #521 Add utils  │  │ Queued:      3   │
│ #522 Fix bug    │  │ Active:      1   │
│ #523 New API    │  │ Completed:  12   │
└─────────────────┘  │ Merged:      5   │
                     └──────────────────┘
┌─ Active Issues ────────────────────────┐
│ #521  ⚡ Executing    45s  Generating...│
└────────────────────────────────────────┘

┌─ PR Monitoring ────────────────────────┐
│ #145  ✅ ✅  ✓ Ready                  │
│ #146  ✅ ⏳  ⏳ Reviews               │
└────────────────────────────────────────┘

┌─ Activity Log ─────────────────────────┐
│ ✅ [14:30:15] Code generated           │
│ 🔨 [14:30:20] Build verification...    │
│ ✅ [14:30:45] Build passed!            │
│ 🚀 [14:30:50] PR #145 created          │
└────────────────────────────────────────┘
```

## CLI Options Reference

| Option | Description |
|--------|-------------|
| `--no-claude-cli` | Disable Claude CLI (if rate-limited) |
| `--no-copilot-cli` | Disable Copilot CLI |
| `--dry-run` | Simulate without changes |
| `--no-dashboard` | Run without live UI |
| `--issue 521` | Process specific issue only |

## Cost Control

**Zero API Credit Mode** (default):
```bash
USE_CLAUDE_CLI=true      # CLI only (no API)
USE_COPILOT_CLI=true     # CLI only (no API)
USE_CLAUDE_API=false     # Disabled!
```

**Cost**: ~$0.01 per issue (Perplexity only)

## Safety Features

- ✅ **Dry Run Mode** - Test without changes
- ✅ **Git Worktrees** - Isolated development
- ✅ **Build Verification** - Auto-rollback on fail
- ✅ **Manual Approval** - Review before merge
- ✅ **Comprehensive Logs** - Full audit trail

## Troubleshooting

### Claude Rate Limited?
```bash
python -m src.main --no-claude-cli
```

### Copilot Not Installed?
```bash
# Disable it
USE_COPILOT_CLI=false

# Or install
gh extension install github/gh-copilot
```

### Build Failed?
```bash
# Check worktree
cd .worktrees/issue-521
npm run build

# View generated code
cat src/utils/stringHelpers.ts
```

## Next Steps

1. **Read the full guide**: [USAGE.md](USAGE.md)
2. **Configure settings**: Edit `.env` for your needs
3. **Test with dry run**: `python -m src.main --dry-run`
4. **Process an issue**: Add `status:ai-ready` label to GitHub issue
5. **Monitor dashboard**: Watch live processing

## Support

- **Documentation**: [README.md](README.md) | [USAGE.md](USAGE.md)
- **Issues**: https://github.com/willtwilson/orchestratorai/issues
- **Repository**: https://github.com/willtwilson/orchestratorai

---

**Ready to automate your development workflow? Let's go! 🚀**
