"""Perplexity API client for research and context gathering."""

import requests
from typing import Dict, Optional


class PerplexityClient:
    """Client for Perplexity AI research."""

    def __init__(self, api_key: str):
        """Initialize Perplexity client.

        Args:
            api_key: Perplexity API key
        """
        self.api_key = api_key
        self.base_url = "https://api.perplexity.ai"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

    def research(self, title: str, description: str) -> Dict:
        """Research a topic using Perplexity.

        Args:
            title: Issue title
            description: Issue description

        Returns:
            Dictionary containing research findings
        """
        prompt = self._build_research_prompt(title, description)

        url = f"{self.base_url}/chat/completions"
        data = {
            "model": "llama-3.1-sonar-small-128k-online",
            "messages": [
                {
                    "role": "system",
                    "content": "You are a research assistant helping gather context for software development tasks."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.2,
            "max_tokens": 2000
        }

        try:
            response = requests.post(url, headers=self.headers, json=data)
            response.raise_for_status()
            result = response.json()

            return {
                "findings": result["choices"][0]["message"]["content"],
                "citations": result.get("citations", [])
            }

        except requests.exceptions.RequestException as e:
            # Fallback to empty context if research fails
            return {
                "findings": "No additional context available.",
                "citations": []
            }

    def _build_research_prompt(self, title: str, description: str) -> str:
        """Build a research prompt from issue details.

        Args:
            title: Issue title
            description: Issue description

        Returns:
            Formatted research prompt
        """
        return f"""Research the following software development task:

Title: {title}

Description:
{description}

Please provide:
1. Relevant technical documentation
2. Best practices and common patterns
3. Potential pitfalls or edge cases
4. Recent developments or updates in related technologies

Focus on actionable information that would help implement this feature or fix this bug.
"""
