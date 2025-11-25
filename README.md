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
# Edit .env with your API keys

# 3. Start the orchestrator
python run.py
```

That's it! The orchestrator will:
- ✅ Monitor issues with `status:ai-ready` label
- ✅ Generate code using CLI tools
- ✅ Create PRs automatically
- ✅ Show live dashboard with real-time status

---

## 📊 Live Dashboard

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                   🤖 OrchestratorAI - Autonomous Development                  ║
║                              2025-11-25 13:48:45                              ║
╚══════════════════════════════════════════════════════════════════════════════╝

╭─ 📋 Queued Issues (3) ──────────────╮  ╭─ 📊 Statistics ─────────────────╮
│ #524  Add user authentication       │  │ 📋 Queued        3              │
│ #525  Fix navigation bug             │  │ ⚙️  Active        1              │
│ #526  Improve loading performance    │  │ ✅ Completed     12             │
╰──────────────────────────────────────╯  │ 🚀 Auto-Merged   3              │
                                          │ ⏱️  Avg Time      5m 32s         │
╭─ ⚙️  Active Issues (1) ─────────────╮  ╰──────────────────────────────────╯
│ #     Status        Duration Details │
│ #521  👀 Reviews    3m 15s   PR #522 │  ╭─ 🔍 PR Monitoring (1) ─────────╮
╰──────────────────────────────────────╯  │ PR   Reviews Status             │
                                          │ #522 ✅ ✅     ✓ Ready          │
╭─ 📜 Activity Log (10) ───────────────────────────────────────────────────────╮
│ ✅ [13:45:12] PR #522 ready to merge                                         │
│ ℹ️  [13:44:58] Perplexity review completed                                   │
│ ℹ️  [13:44:32] Copilot review completed                                      │
│ ✅ [13:42:15] PR #522 created successfully                                   │
│ ℹ️  [13:41:50] Build passed for issue #521                                   │
╰───────────────────────────────────────────────────────────────────────────────╯
```

---

## 🏗️ Architecture

## Overview

OrchestratorAI is an intelligent automation system that bridges the gap between issue tracking and code implementation. It uses:

- **Claude Code** for intelligent planning and task breakdown
- **GitHub Copilot** for code execution and implementation
- **Perplexity** for research and context gathering
- **Vercel** for automated deployments and QA
- **Rich** for beautiful terminal dashboards

## Features

- Automated GitHub issue processing
- AI-powered planning with Claude Code
- Code generation and execution with GitHub Copilot
- Real-time terminal dashboard with task status
- Automated build verification
- Vercel deployment integration
- Git worktree management for parallel issue handling

## Installation

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
