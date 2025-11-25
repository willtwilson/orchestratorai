"""Claude Code agent for intelligent planning."""

import requests
import subprocess
import os
from pathlib import Path
from typing import Dict, List


class ClaudeAgent:
    """Agent for creating implementation plans using Claude Code CLI (NOT API)."""

    def __init__(self, api_key: str):
        """Initialize Claude agent.

        Args:
            api_key: Anthropic API key (only used if USE_CLAUDE_API=true in .env)
        """
        self.api_key = api_key
        self.base_url = "https://api.anthropic.com/v1"
        self.headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }
        self.model = "claude-sonnet-4-5-20250929"
        self.use_api = os.getenv("USE_CLAUDE_API", "false").lower() == "true"
        
        if self.use_api:
            print("⚠️  WARNING: Claude API is enabled! This will consume API credits.")
            print("⚠️  Set USE_CLAUDE_API=false in .env to use CLI only.")
        else:
            print("✅ Claude API disabled. Using CLI only (no API credits consumed).")

    def create_plan(self, issue: Dict, context: Dict) -> Dict:
        """Create an implementation plan for an issue using CLI (or API if enabled).

        Args:
            issue: GitHub issue dictionary
            context: Research context from Perplexity

        Returns:
            Implementation plan dictionary
        """
        prompt = self._build_planning_prompt(issue, context)
        
        # Try Claude Code CLI first (no API credits)
        if not self.use_api:
            print("[CLAUDE] Using Claude Code CLI for planning (no API credits)...")
            try:
                plan_text = self._create_plan_with_cli(prompt)
            except Exception as e:
                print(f"[CLAUDE CLI] Failed: {e}")
                print("[FALLBACK] Creating simple plan without AI...")
                plan_text = self._create_simple_plan(issue, context)
        else:
            # Only use API if explicitly enabled
            print("[CLAUDE API] Using Anthropic API (consuming credits)...")
            plan_text = self._create_plan_with_api(prompt)

        return {
            "issue_number": issue["number"],
            "title": issue["title"],
            "description": plan_text,
            "steps": self._extract_steps(plan_text),
            "files_to_modify": self._extract_files(plan_text)
        }
    
    def _create_plan_with_cli(self, prompt: str) -> str:
        """Create plan using Claude Code CLI (no API credits).
        
        Args:
            prompt: Planning prompt
            
        Returns:
            Plan text
        """
        # Write prompt to temp file
        temp_file = Path("data/.claude_planning_prompt.txt")
        temp_file.parent.mkdir(exist_ok=True)
        temp_file.write_text(prompt, encoding='utf-8')
        
        try:
            # Try 'claude' CLI command
            result = subprocess.run(
                ["claude", "chat", f"@{temp_file}"],
                capture_output=True,
                text=True,
                timeout=60,
                encoding='utf-8',
                errors='replace'
            )
            
            if result.returncode == 0 and result.stdout:
                print(f"[CLAUDE CLI] Received plan ({len(result.stdout)} chars)")
                return result.stdout
            else:
                raise Exception(f"CLI failed: {result.stderr[:200]}")
                
        except FileNotFoundError:
            raise Exception("'claude' command not found. Install with: npm install -g @anthropic-ai/claude-cli")
        except subprocess.TimeoutExpired:
            raise Exception("Claude CLI timed out after 60s")
        finally:
            # Clean up temp file
            if temp_file.exists():
                temp_file.unlink()
    
    def _create_plan_with_api(self, prompt: str) -> str:
        """Create plan using Anthropic API (consumes API credits).
        
        Args:
            prompt: Planning prompt
            
        Returns:
            Plan text
        """
        url = f"{self.base_url}/messages"
        data = {
            "model": self.model,
            "max_tokens": 4096,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.3
        }

        response = requests.post(url, headers=self.headers, json=data)
        response.raise_for_status()
        result = response.json()

        return result["content"][0]["text"]
    
    def _create_simple_plan(self, issue: Dict, context: Dict) -> str:
        """Create a simple plan without AI when CLI/API unavailable.
        
        Args:
            issue: GitHub issue
            context: Research context
            
        Returns:
            Simple plan text
        """
        return f"""## Implementation Plan

### Issue: {issue['title']}

{issue.get('body', 'No description provided')}

### Research Findings:
{context.get('findings', 'No research available')}

### Implementation Steps:
1. Review the issue requirements
2. Identify files that need to be created or modified
3. Implement the changes following TypeScript best practices
4. Add appropriate tests
5. Verify build passes
6. Create pull request

### Files to Modify:
- Based on issue description

### Testing Strategy:
- Unit tests for new functionality
- Integration tests if needed
- Manual verification

### Risks:
- Review dependencies carefully
- Ensure backward compatibility
"""

    def _build_planning_prompt(self, issue: Dict, context: Dict) -> str:
        """Build a planning prompt.

        Args:
            issue: GitHub issue
            context: Research context

        Returns:
            Planning prompt
        """
        return f"""You are an expert software architect creating a detailed implementation plan.

Issue: {issue['title']}

Description:
{issue['body']}

Research Context:
{context['findings']}

Create a detailed implementation plan that includes:
1. Overview of the changes needed
2. Step-by-step implementation steps
3. Files that need to be modified or created
4. Testing strategy
5. Potential risks or challenges

Format your response as a clear, actionable plan that a developer can follow.
Use markdown formatting with clear sections.
"""

    def _extract_steps(self, plan_text: str) -> List[str]:
        """Extract implementation steps from plan.

        Args:
            plan_text: Plan text

        Returns:
            List of steps
        """
        # Simple extraction - can be enhanced with better parsing
        steps = []
        lines = plan_text.split('\n')
        for line in lines:
            if line.strip().startswith(('1.', '2.', '3.', '4.', '5.', '-', '*')):
                steps.append(line.strip())
        return steps

    def _extract_files(self, plan_text: str) -> List[str]:
        """Extract file paths from plan.

        Args:
            plan_text: Plan text

        Returns:
            List of file paths
        """
        # Simple extraction - looks for common file patterns
        import re
        file_pattern = r'`([a-zA-Z0-9_/\-\.]+\.[a-zA-Z0-9]+)`'
        matches = re.findall(file_pattern, plan_text)
        return list(set(matches))
