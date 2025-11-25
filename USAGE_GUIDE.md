# OrchestratorAI - Usage Guide

## Quick Start

### Prerequisites
- Python 3.11+
- GitHub CLI (`gh`) authenticated
- GitHub Copilot CLI extension (optional but recommended)
- Claude CLI (optional but recommended)

### Installation

```bash
# Clone the repository
git clone https://github.com/willtwilson/orchestratorai.git
cd orchestratorai

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment
cp .env.example .env
# Edit .env with your API keys
```

### Running the Application

```bash
# Start with interactive menu (recommended)
python -m src.main

# Or with command-line options
python -m src.main --no-claude-cli     # Disable Claude if rate-limited
python -m src.main --no-copilot-cli    # Disable Copilot if unavailable
python -m src.main --dry-run           # Test mode, no changes
python -m src.main --issue 521         # Process specific issue
```

## 🎯 Main Menu Options

When you run `python -m src.main`, you'll see:

```
1. 🚀 Start Orchestration    - Process all AI-ready issues
2. 🎯 Process Single Issue   - Work on a specific issue
3. 📊 Show Dashboard         - View live status
4. 🔍 Monitor PR             - Monitor PR reviews
5. ⚙️  Settings              - Configure agents
6. 📋 List Issues            - View AI-ready issues
7. 🧪 Test Mode              - Dry run (no changes)
0. ❌ Exit                   - Quit
```

## 🤖 AI Agent Configuration

### CLI-Based (No API Credits - Default)

The app uses CLI commands by default:
- **Claude CLI**: `claude` command (for planning)
- **Copilot CLI**: `copilot` or `gh copilot` (for code generation)

These do NOT consume API credits!

### Temporary Disabling

If Claude Code is rate-limited:
```bash
python -m src.main --no-claude-cli
```

If Copilot is unavailable:
```bash
python -m src.main --no-copilot-cli
```

The app will fallback to simple template generation (no AI).

### API Fallback (Uses Credits - Disabled by Default)

Only enable if you want to use the Anthropic API:

In `.env`:
```bash
USE_CLAUDE_API=true  # WARNING: Consumes API credits!
```

Or in Settings menu (option 5).

## 📊 Dashboard Features

The live dashboard shows:
- **Stats**: Queued, Active, Done, Failed, Merged counts
- **Active Issues**: Currently being processed with status
- **Queued Issues**: Next 3 issues to process
- **PR Status**: Review status for monitored PRs
- **Logs**: Last 4 activity messages

Dashboard is compact and fits on half screen.

## 🔍 PR Monitoring

The orchestrator automatically:
1. Creates PRs after successful builds
2. Monitors for reviews (GitHub Copilot + Perplexity)
3. Parses review comments for priority items
4. Creates new issues for deferred items
5. Provides merge recommendations
6. Auto-merges (if AUTOPILOT_MODE=true)

## ⚙️ Configuration

### Environment Variables

```bash
# Required
GITHUB_TOKEN=ghp_xxx          # GitHub personal access token
GITHUB_REPO=owner/repo        # Target repository
PERPLEXITY_API_KEY=pplx_xxx   # Perplexity API key

# Optional
ANTHROPIC_API_KEY=sk-ant-xxx  # Only if USE_CLAUDE_API=true
CLARIUM_PATH=/path/to/clarium # Path to target repo

# Code Generation (CLI by default, no API credits)
USE_CLAUDE_CLI=true           # Use Claude CLI (default)
USE_COPILOT_CLI=true          # Use Copilot CLI (default)
USE_CLAUDE_API=false          # Use Anthropic API (disabled by default)

# Safety
DRY_RUN=false                 # Simulate without changes
REQUIRE_HUMAN_APPROVAL=true   # Require human review before merge

# Automation
AUTOPILOT_MODE=false          # Auto-merge when ready (use with caution)
AUTO_CREATE_PR=true           # Auto-create PRs after builds
PR_MONITORING_ENABLED=true    # Monitor PRs for reviews
```

## 🚀 Workflow

### Typical Flow

1. User labels GitHub issue with `status:ai-ready`
2. Orchestrator detects issue
3. Perplexity researches requirements
4. Claude creates implementation plan
5. Copilot/Claude CLI generates code
6. Build verification runs
7. PR created automatically
8. Reviews monitored (Copilot + Perplexity)
9. Merge recommendation provided
10. Human reviews and merges (or auto-merge if AUTOPILOT_MODE=true)

### Manual Testing

```bash
# Create test issue
gh issue create \
  --title "Test: Add simple utility" \
  --body "Add a capitalize function" \
  --label "status:ai-ready"

# Run orchestrator in test mode
python -m src.main --dry-run

# Or interactively
python -m src.main
# Select option 7 (Test Mode)
```

## 🛡️ Safety Features

1. **Dry Run Mode**: Test without making changes
2. **Git Worktrees**: Isolated development environments
3. **Build Verification**: Code must build before PR creation
4. **Review Monitoring**: Wait for reviews before merge
5. **Human Approval**: Require manual approval (configurable)
6. **Rate Limit Handling**: Graceful fallbacks when CLIs unavailable

## 🔧 Troubleshooting

### Claude CLI Rate Limited

```bash
# Temporarily disable
python -m src.main --no-claude-cli
```

### Copilot CLI Not Available

```bash
# Install
gh extension install github/gh-copilot

# Or disable
python -m src.main --no-copilot-cli
```

### Build Failures

Check worktree directory:
```bash
cd .worktrees/issue-XXX
npm run build  # See detailed error
```

### Dashboard Not Fitting Screen

Dashboard is now compact (23 lines total):
- Reduce terminal font size if needed
- Or run without dashboard: `python -m src.main --no-dashboard`

## 📝 API Credit Usage

### CLI Mode (Default)
- **Perplexity**: ~$0.01 per issue (research)
- **Claude CLI**: FREE (no API credits)
- **Copilot CLI**: FREE (no API credits)
- **Total per issue**: ~$0.01

### API Mode (If Enabled)
- **Perplexity**: ~$0.01 per issue
- **Claude API**: ~$0.03 per issue (planning + code gen)
- **Total per issue**: ~$0.04

**Recommendation**: Use CLI mode to minimize costs!

## 🎉 Success Indicators

When processing completes successfully:

✅ Code generated
✅ Build passed
✅ PR created
✅ Reviews monitored
✅ Merge recommendation provided

Check dashboard or GitHub for PR link.

## 📞 Support

- GitHub Issues: https://github.com/willtwilson/orchestratorai/issues
- Documentation: See markdown files in repository root

---

**Happy Orchestrating! 🤖**
