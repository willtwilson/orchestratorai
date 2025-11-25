"""GitHub API client for issue and repository management."""

import requests
from typing import List, Dict, Optional


class GitHubClient:
    """Client for interacting with GitHub API."""

    def __init__(self, token: str, repo: str, dry_run: bool = False):
        """Initialize GitHub client.

        Args:
            token: GitHub personal access token
            repo: Repository in format 'owner/repo'
            dry_run: If True, only simulate actions without making changes
        """
        self.token = token
        self.repo = repo
        self.dry_run = dry_run
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }

    def get_open_issues(self, labels: Optional[List[str]] = None) -> List[Dict]:
        """Fetch all open issues from the repository.

        Args:
            labels: Optional list of labels to filter by (e.g., ["status:ai-ready"])

        Returns:
            List of issue dictionaries
        """
        url = f"{self.base_url}/repos/{self.repo}/issues"
        params = {
            "state": "open",
            "per_page": 100
        }
        
        # Add label filter if provided
        if labels:
            params["labels"] = ",".join(labels)

        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()

        # Filter out pull requests (they appear in issues endpoint)
        issues = [
            issue for issue in response.json()
            if "pull_request" not in issue
        ]

        return issues

    def get_ai_ready_issues(self) -> List[Dict]:
        """Fetch all issues with status:ai-ready label.
        
        Returns:
            List of AI-ready issue dictionaries
        """
        return self.get_open_issues(labels=["status:ai-ready"])

    def get_issue(self, issue_number: int) -> Dict:
        """Fetch a specific issue.

        Args:
            issue_number: Issue number

        Returns:
            Issue dictionary
        """
        url = f"{self.base_url}/repos/{self.repo}/issues/{issue_number}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def add_comment(self, issue_number: int, comment: str):
        """Add a comment to an issue.

        Args:
            issue_number: Issue number
            comment: Comment text
        """
        if self.dry_run:
            print(f"🔒 [DRY RUN] Would add comment to issue #{issue_number}:")
            print(f"   {comment[:100]}...")
            return

        url = f"{self.base_url}/repos/{self.repo}/issues/{issue_number}/comments"
        data = {"body": comment}

        response = requests.post(url, headers=self.headers, json=data)
        response.raise_for_status()

    def create_pull_request(
        self,
        issue_number: int,
        title: str,
        description: str,
        head_branch: Optional[str] = None
    ) -> Dict:
        """Create a pull request.

        Args:
            issue_number: Related issue number
            title: PR title
            description: PR description
            head_branch: Source branch (defaults to issue-{issue_number})

        Returns:
            Pull request dictionary
        """
        if head_branch is None:
            head_branch = f"issue-{issue_number}"

        if self.dry_run:
            print(f"🔒 [DRY RUN] Would create PR:")
            print(f"   Title: {title}")
            print(f"   Branch: {head_branch} -> main")
            print(f"   Closes: #{issue_number}")
            return {"number": 0, "html_url": "https://github.com/dry-run/pr/0"}

        url = f"{self.base_url}/repos/{self.repo}/pulls"
        data = {
            "title": title,
            "body": f"{description}\n\nCloses #{issue_number}",
            "head": head_branch,
            "base": "main"
        }

        response = requests.post(url, headers=self.headers, json=data)
        response.raise_for_status()
        return response.json()

    def update_issue(
        self,
        issue_number: int,
        state: Optional[str] = None,
        labels: Optional[List[str]] = None
    ):
        """Update an issue.

        Args:
            issue_number: Issue number
            state: New state ('open' or 'closed')
            labels: List of label names
        """
        if self.dry_run:
            print(f"🔒 [DRY RUN] Would update issue #{issue_number}:")
            if state:
                print(f"   State: {state}")
            if labels:
                print(f"   Labels: {labels}")
            return

        url = f"{self.base_url}/repos/{self.repo}/issues/{issue_number}"
        data = {}

        if state:
            data["state"] = state
        if labels is not None:
            data["labels"] = labels

        response = requests.patch(url, headers=self.headers, json=data)
        response.raise_for_status()

    def create_branch(self, branch_name: str, from_branch: str = "main") -> bool:
        """Create a new branch.

        Args:
            branch_name: Name of the new branch
            from_branch: Source branch to branch from

        Returns:
            True if successful
        """
        if self.dry_run:
            print(f"🔒 [DRY RUN] Would create branch:")
            print(f"   {from_branch} -> {branch_name}")
            return True

        # Get the SHA of the source branch
        ref_url = f"{self.base_url}/repos/{self.repo}/git/refs/heads/{from_branch}"
        response = requests.get(ref_url, headers=self.headers)
        response.raise_for_status()
        sha = response.json()["object"]["sha"]

        # Create the new branch
        url = f"{self.base_url}/repos/{self.repo}/git/refs"
        data = {
            "ref": f"refs/heads/{branch_name}",
            "sha": sha
        }

        response = requests.post(url, headers=self.headers, json=data)
        response.raise_for_status()
        return True
