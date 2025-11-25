# 🤖 OrchestratorAI

**Autonomous AI Development Pipeline with Live Dashboard**

[![Status](https://img.shields.io/badge/status-production--ready-brightgreen.svg)]()
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)]()
[![License](https://img.shields.io/badge/license-MIT-blue.svg)]()

Fully autonomous system that processes GitHub issues using AI agents, generates code with CLI tools (no API costs), verifies builds, creates PRs, monitors reviews, and recommends merges—all with a beautiful live terminal dashboard.

---

## ✨ Features

- 🔍 **Intelligent Research** - Perplexity API analyzes issue context
- 📋 **Smart Planning** - Claude Code CLI creates implementation plans
- ⚡ **Code Generation** - GitHub Copilot CLI generates TypeScript code
- 🔨 **Build Verification** - Automatic npm build checks
- 🚀 **PR Automation** - Creates and manages pull requests
- 👀 **Review Monitoring** - Tracks Copilot and Perplexity reviews
- 🧠 **Merge Intelligence** - Analyzes reviews and recommends decisions
- 📊 **Live Dashboard** - Real-time status with Rich terminal UI
- 💰 **Cost Efficient** - ~$0.01 per issue (CLI-based, minimal API usage)
- 🛡️ **Safety First** - Dry run mode, worktree isolation, manual approval

---

## 🚀 Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# Edit .env with your API keys and paths

# 3. Install CLI tools (at least one)
npm install -g @anthropic-ai/claude-cli  # For Claude Code
gh extension install github/gh-copilot    # For GitHub Copilot

# 4. Start the orchestrator (smart start)
python start.py
```

**Alternative Direct Start:**
```bash
python -m src.main
```

The smart start (`start.py`) will:
- ✅ Auto-detect available CLI tools
- ✅ Configure runtime settings dynamically
- ✅ Disable API usage by default (no API charges!)
- ✅ Warn if CLI tools are missing

---

## 📊 Live Dashboard (Compact Design)

The dashboard is designed to fit in half your screen (≈31 lines):

```
╔═══════════════════════════════════════════════════════════════╗
║      🤖 OrchestratorAI - Autonomous Pipeline | 14:55:23      ║
╚═══════════════════════════════════════════════════════════════╝

╭─ 📊 Stats ─────╮  ╭─ 📋 Queued (3) ────────────────────╮
│ Queue     3    │  │ #524 Add user authentication       │
│ Active    1    │  │ #525 Fix navigation bug            │
│ Done      12   │  │ #526 Improve loading performance   │
│ Merge     3    │  ╰────────────────────────────────────╯
╰────────────────╯
                    ╭─ 🔍 PRs (1) ──────────────────────╮
╭─ ⚙️ Active (1) ─╮  │ #522  ✓✓  ✓ Ready               │
│ #521  👀 Review │  ╰────────────────────────────────────╯
│         3m      │
╰─────────────────╯

╭─ 📜 Log (6) ──────────────────────────────────────────────╮
│ ✅ 14:45 PR #522 ready to merge                          │
│ ℹ 14:44 Perplexity review completed                      │
│ ℹ 14:44 Copilot review completed                         │
│ ✅ 14:42 PR #522 created successfully                    │
╰───────────────────────────────────────────────────────────╯
```

Features:
- 🎯 **Compact**: Fits in half-screen vertical split
- ⚡ **Smooth**: 1Hz refresh (no bounce/flicker)
- 📊 **Info-dense**: Shows all critical metrics
- 🎨 **Color-coded**: Status at a glance

---

## 💰 Cost Efficiency

### CLI-Based (No API Charges)
- **Claude CLI**: Uses Claude Code subscription (no per-request fees)
- **Copilot CLI**: Uses GitHub Copilot subscription
- **Perplexity API**: ~$0.01 per issue for research
  - Total for 70 issues: **~$0.70**

### API Protection Built-In
- ✅ Claude API disabled by default (`USE_CLAUDE_API=false`)
- ✅ Auto-detects available CLI tools on startup
- ✅ Fallback to simple generation if no CLI available
- ⚠️ Only enable API for emergencies

---

## 🏗️ Architecture

## 🏗️ Architecture

### Component Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    GitHub Issues                            │
│              (labeled: status:ai-ready)                     │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                  OrchestratorAI                             │
│  ┌──────────────┐  ┌───────────────┐  ┌─────────────────┐ │
│  │  Perplexity  │→ │  Claude CLI   │→ │  Copilot CLI    │ │
│  │   Research   │  │   Planning    │  │   Generation    │ │
│  └──────────────┘  └───────────────┘  └─────────────────┘ │
│         │                  │                    │          │
│         └──────────────────┼────────────────────┘          │
│                            ▼                               │
│                   ┌────────────────┐                       │
│                   │ Build Verify   │                       │
│                   └────────┬───────┘                       │
│                            ▼                               │
│                   ┌────────────────┐                       │
│                   │   Create PR    │                       │
│                   └────────┬───────┘                       │
│                            ▼                               │
│                   ┌────────────────┐                       │
│                   │ Monitor Reviews│                       │
│                   └────────┬───────┘                       │
│                            ▼                               │
│                   ┌────────────────┐                       │
│                   │Merge Decision  │                       │
│                   └────────────────┘                       │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
                 ┌──────────────────────┐
                 │    Live Dashboard    │
                 │  (Real-time Status)  │
                 └──────────────────────┘
```

### Key Components

1. **Perplexity Research** - Analyzes issue complexity and technical approach
2. **Claude CLI Planning** - Creates detailed implementation plans
3. **Copilot CLI Generation** - Generates TypeScript code from plans
4. **Build Verification** - Runs npm build to verify changes
5. **PR Management** - Creates and tracks pull requests
6. **Review Monitoring** - Waits for AI reviews (Copilot + Perplexity)
7. **Merge Intelligence** - Analyzes reviews and recommends merge decisions
8. **Live Dashboard** - Shows real-time status of all operations

---

## 📋 Prerequisites

### Required
- Python 3.11+
- Git
- Node.js & npm (for Clarium repo builds)
- GitHub CLI (`gh`)

### AI Tools (install at least one)
- **Claude CLI**: `npm install -g @anthropic-ai/claude-cli`
- **GitHub Copilot CLI**: `gh extension install github/gh-copilot`

### API Keys
- `PERPLEXITY_API_KEY` - For research (costs ~$0.01/issue)
- `GITHUB_TOKEN` - For GitHub API access
- `ANTHROPIC_API_KEY` - Optional emergency fallback

---

## 🎯 Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd orchestratorai
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

Or using the project in development mode:
```bash
pip install -e ".[dev]"
```

3. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys and configuration
```

## Configuration

Required environment variables in `.env`:

- `GITHUB_TOKEN` - GitHub personal access token with repo access
- `GITHUB_REPO` - Repository in format `owner/repo`
- `ANTHROPIC_API_KEY` - Anthropic API key for Claude
- `COPILOT_TOKEN` - GitHub Copilot access token
- `PERPLEXITY_API_KEY` - Perplexity API key for research

Optional:
- `VERCEL_TOKEN` - Vercel API token for deployments
- `VERCEL_PROJECT_ID` - Vercel project identifier
- `LOG_LEVEL` - Logging level (default: INFO)
- `MAX_CONCURRENT_ISSUES` - Maximum parallel issues (default: 3)

## Usage

Run the orchestrator:

```bash
python -m orchestratorai
```

Or if installed:

```bash
orchestratorai
```

## Project Structure

```
orchestratorai/
├── src/
│   ├── main.py              # Entry point
│   ├── orchestrator.py      # Main orchestration logic
│   ├── agents/
│   │   ├── claude.py        # Claude Code integration
│   │   └── copilot.py       # GitHub Copilot integration
│   ├── qa/
│   │   ├── build.py         # Build verification
│   │   └── vercel.py        # Vercel deployment
│   ├── github_client.py     # GitHub API client
│   ├── perplexity.py        # Perplexity research client
│   └── dashboard.py         # Rich terminal dashboard
├── data/                     # Runtime data and state
└── tests/                    # Test suite
```

## How It Works

1. **Issue Discovery**: Monitors GitHub repository for open issues
2. **Planning**: Claude Code analyzes issues and creates implementation plans
3. **Research**: Perplexity gathers relevant context and documentation
4. **Execution**: GitHub Copilot implements the planned changes
5. **Verification**: Automated build and test execution
6. **Deployment**: Optional Vercel deployment for web projects
7. **Feedback**: Updates GitHub issues with progress and results

## Development

Run tests:
```bash
pytest
```

Format code:
```bash
black src/
```

Lint:
```bash
ruff check src/
```

## License

MIT License

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.
