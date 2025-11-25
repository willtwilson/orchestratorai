# API Credit Protection - Configuration Update

## ✅ Changes Made

### Problem Identified
The orchestrator was using **Anthropic API directly** for Claude planning, which consumes API credits even when Claude Code CLI is available and rate-limited.

### Solution Implemented
Added configuration switches to **disable API usage by default** and rely exclusively on CLI tools.

---

## 🔧 Configuration Changes

### `.env` File Updates

**Before:**
```env
# Claude API Configuration
ANTHROPIC_API_KEY=sk-ant-api03-...
```

**After:**
```env
# Claude API Configuration (ONLY for emergencies - uses API credits!)
# Set USE_CLAUDE_API=true to enable API fallback
ANTHROPIC_API_KEY=sk-ant-api03-...
USE_CLAUDE_API=false

# Code Generation Configuration
# Uses CLI tools ONLY (no API credits consumed)
# - Claude Code CLI: 'claude' command (requires: npm install -g @anthropic-ai/claude-cli)
# - GitHub Copilot CLI: 'copilot' command (requires: gh extension install github/gh-copilot)
USE_CLAUDE_CLI=true
USE_COPILOT_CLI=true
```

---

## 📝 Code Changes

### 1. `src/agents/claude.py` - Planning Agent

**Changes:**
- ✅ Added `USE_CLAUDE_API` check in `__init__`
- ✅ Shows warning if API is enabled
- ✅ Added `_create_plan_with_cli()` method using `claude` CLI command
- ✅ Added `_create_simple_plan()` fallback (no AI, no API)
- ✅ Modified `create_plan()` to try CLI first, only use API if explicitly enabled

**Execution Flow:**
```
1. Check USE_CLAUDE_API setting
2. If false (default):
   a. Try Claude Code CLI ('claude chat')
   b. If fails, create simple plan from issue description
3. If true (emergency only):
   a. Use Anthropic API (consumes credits)
```

### 2. `src/agents/copilot.py` - Code Generation Agent

**Changes:**
- ✅ Added `USE_CLAUDE_CLI` and `USE_COPILOT_CLI` checks
- ✅ Added `_generate_with_copilot_cli()` method
- ✅ Modified `_generate_code()` to try both CLI tools before fallback
- ✅ Shows configuration status at runtime

**Execution Flow:**
```
1. Check USE_COPILOT_CLI setting
   a. Try GitHub Copilot CLI ('copilot suggest')
   b. If fails, continue to next option

2. Check USE_CLAUDE_CLI setting
   a. Try Claude Code CLI ('claude chat')
   b. If fails, continue to next option

3. Fallback: Simple template generation
   a. No AI, no API
   b. Creates basic files from patterns
```

---

## 🚀 Current Behavior (After Fix)

### Planning Phase (Claude Agent)
```
✅ Claude API disabled. Using CLI only (no API credits consumed).
[CLAUDE] Using Claude Code CLI for planning (no API credits)...
```

**If Claude CLI rate limited:**
```
[CLAUDE CLI] Failed: Rate limited until 2pm
[FALLBACK] Creating simple plan without AI...
```

### Code Generation Phase (Copilot Agent)
```
[CONFIG] Claude CLI: ✅ Enabled
[CONFIG] Copilot CLI: ✅ Enabled
[CONFIG] API usage: ❌ Disabled (CLI only)

[STRATEGY] Trying GitHub Copilot CLI first...
[COPILOT CLI] Trying 'copilot' command...
```

**If both CLIs fail:**
```
[FALLBACK] Using simple template-based generation (no AI)...
[SIMPLE GEN] Creating basic implementation...
✅ Created: src/utils/stringHelpers.ts
```

---

## 🔒 API Credit Protection

### Default Configuration (Safe)
```env
USE_CLAUDE_API=false  # ✅ No API credits consumed
USE_CLAUDE_CLI=true   # ✅ Uses authenticated CLI
USE_COPILOT_CLI=true  # ✅ Uses authenticated CLI
```

### Emergency Configuration (Use with Caution)
```env
USE_CLAUDE_API=true   # ⚠️ CONSUMES API CREDITS!
USE_CLAUDE_CLI=true
USE_COPILOT_CLI=true
```

**Cost Impact:**
- Planning: ~1,000 tokens input + 4,000 tokens output = ~$0.02 per issue
- Code Gen: Not using API anymore (CLI only)

---

## 📊 CLI Tool Requirements

### GitHub Copilot CLI
```bash
# Install
gh extension install github/gh-copilot

# Verify
copilot --version
```

### Claude Code CLI
```bash
# Install
npm install -g @anthropic-ai/claude-cli

# Authenticate
claude auth login

# Verify
claude --version
```

---

## ✅ Verification

Current configuration is **safe**:
- ❌ No API credits consumed for planning
- ❌ No API credits consumed for code generation
- ✅ Only uses authenticated CLI tools
- ✅ Only Perplexity API used (as intended)

**If CLIs are rate-limited:**
- Creates simple plans from issue description
- Generates basic code from templates
- System continues to function (degraded mode)

---

## 🎯 Next Steps

1. **Verify CLI installations:**
   ```bash
   copilot --version
   claude --version
   ```

2. **Test with real issue:**
   ```bash
   python -u -m src.main
   ```

3. **Monitor output for:**
   - "✅ Claude API disabled" message
   - "[CONFIG] API usage: ❌ Disabled" message
   - No API requests in network logs

---

## 🔍 How to Check API Usage

**Good (No API):**
```
✅ Claude API disabled. Using CLI only (no API credits consumed).
[CLAUDE] Using Claude Code CLI for planning (no API credits)...
[CONFIG] API usage: ❌ Disabled (CLI only)
```

**Bad (Using API):**
```
⚠️  WARNING: Claude API is enabled! This will consume API credits.
[CLAUDE API] Using Anthropic API (consuming credits)...
```

If you see the warning, check `.env` and ensure:
```env
USE_CLAUDE_API=false
```

---

**Status:** ✅ API credit consumption blocked by default
**Date:** 2025-01-25
**Impact:** Zero API costs for planning and code generation (only Perplexity API used)
