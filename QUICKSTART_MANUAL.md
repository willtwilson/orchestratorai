# 🚀 OrchestratorAI - Quick Start Guide

## Starting the Orchestrator

### Method 1: Smart Start (Recommended)
The smart start script automatically detects available CLI tools:

```bash
python start.py
```

This will:
- ✅ Check which CLI tools are installed (claude, copilot, gh copilot)
- ✅ Auto-configure the orchestrator to use available tools
- ✅ Disable API usage by default (no API credits consumed)
- ✅ Warn if no CLI tools are found

### Method 2: Direct Start
Run the orchestrator directly:

```bash
python -m src.main
```

### Method 3: Custom Configuration
Override CLI usage via environment variables:

```bash
# Temporarily disable Claude CLI (e.g., during rate limit)
$env:USE_CLAUDE_CLI="false"
python -m src.main

# Temporarily disable Copilot CLI
$env:USE_COPILOT_CLI="false"
python -m src.main

# Emergency: Enable API (consumes credits!)
$env:USE_CLAUDE_API="true"
python -m src.main
```

## CLI Tool Installation

### Claude CLI
```bash
npm install -g @anthropic-ai/claude-cli
claude auth  # Authenticate with your account
```

### GitHub Copilot CLI
```bash
gh extension install github/gh-copilot
gh auth login  # If not already authenticated
```

## CLI Rate Limits

### Claude Code
- Free tier: Limited requests per day
- If rate limited: Use Copilot CLI or wait until reset (typically 2pm UTC)

### GitHub Copilot
- Requires GitHub Copilot subscription
- Generally higher rate limits

## Dashboard Display

The dashboard is designed to fit in half your screen vertically:

```
┌─────────────────────────────────────┐
│ 🤖 OrchestratorAI - Active          │ ← Header (3 lines)
├──────────────┬──────────────────────┤
│ 📊 Stats     │ 📋 Queued            │
│ ⚙️ Active    │ 🔍 PRs               │ ← Main (20 lines)
├──────────────┴──────────────────────┤
│ 📜 Activity Log                     │ ← Footer (8 lines)
└─────────────────────────────────────┘
Total: ~31 lines (fits in 720p vertical)
```

## Configuration Quick Reference

### .env File
```bash
# Core Settings
DRY_RUN=false                    # Set true to test without changes
AUTO_MERGE=false                 # Set true for autopilot mode

# CLI Configuration (auto-detected if not set)
USE_CLAUDE_CLI=true              # Use Claude CLI for planning
USE_COPILOT_CLI=true             # Use Copilot CLI for code generation
USE_CLAUDE_API=false             # IMPORTANT: Keep false to avoid API charges!

# PR Monitoring
PR_MONITORING_ENABLED=true
AUTOPILOT_MODE=false
REQUIRE_HUMAN_APPROVAL=true

# Repository
GITHUB_REPO=willtwilson/clarium
CLARIUM_PATH=C:/Users/willt/Documents/Projects/clarium
```

## Typical Workflow

1. **Create Issue** in GitHub repo with `status:ai-ready` label
2. **Start Orchestrator**: `python start.py`
3. **Monitor Dashboard**: Watch real-time progress
4. **Review PR**: Check generated code and reviews
5. **Merge**: Manually merge or enable autopilot

## Troubleshooting

### "Claude CLI not found"
- Install: `npm install -g @anthropic-ai/claude-cli`
- Or disable: `$env:USE_CLAUDE_CLI="false"`

### "Rate limit exceeded"
- Claude Code resets at 2pm UTC
- Switch to Copilot: `$env:USE_CLAUDE_CLI="false"`
- Or wait for reset

### "No AI tools available"
- Install at least one CLI tool (see above)
- Or accept fallback to simple template generation

### Dashboard too large/small
- Adjust terminal font size
- Dashboard auto-fits to ~31 lines

## API Credit Protection

The orchestrator is designed to **NOT use API credits** by default:

- ✅ Claude CLI: Uses your Claude Code subscription (no per-request charges)
- ✅ Copilot CLI: Uses your GitHub Copilot subscription
- ❌ Claude API: Only used if `USE_CLAUDE_API=true` (emergency fallback)

### Only Perplexity uses API credits
- Used for research/planning only
- Typically < $0.01 per issue
- Total cost for 70 issues: ~$0.70

## Support

For issues or questions:
1. Check logs in dashboard
2. Review `data/state.json` for issue status
3. Check `.worktrees/` for generated code
4. Enable debug logging: `$env:DEBUG="true"`
