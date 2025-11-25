"""Vercel deployment integration for QA."""

import requests
from typing import Dict, Optional


class VercelDeployer:
    """Handles Vercel deployments for preview and testing."""

    def __init__(self, token: Optional[str] = None, project_id: Optional[str] = None, dry_run: bool = False):
        """Initialize Vercel deployer.

        Args:
            token: Vercel API token
            project_id: Vercel project ID
            dry_run: If True, only simulate deployments
        """
        self.token = token
        self.project_id = project_id
        self.dry_run = dry_run
        self.base_url = "https://api.vercel.com"

        if token:
            self.headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
        else:
            self.headers = {}

    def deploy(self, issue_number: int) -> Optional[Dict]:
        """Deploy a preview for an issue.

        Args:
            issue_number: GitHub issue number

        Returns:
            Deployment info or None if not configured
        """
        if not self.token or not self.project_id:
            return None

        if self.dry_run:
            print(f"🔒 [DRY RUN] Would deploy to Vercel:")
            print(f"   Branch: issue-{issue_number}")
            return {"id": "dry-run", "url": "https://dry-run.vercel.app", "status": "ready"}

        try:
            # Trigger deployment
            url = f"{self.base_url}/v13/deployments"
            data = {
                "name": f"issue-{issue_number}",
                "project": self.project_id,
                "target": "preview",
                "gitSource": {
                    "type": "github",
                    "ref": f"issue-{issue_number}"
                }
            }

            response = requests.post(url, headers=self.headers, json=data)
            response.raise_for_status()
            deployment = response.json()

            # Wait for deployment to complete
            deployment_url = self._wait_for_deployment(deployment["id"])

            return {
                "id": deployment["id"],
                "url": deployment_url,
                "status": "ready"
            }

        except Exception as e:
            print(f"Vercel deployment error: {e}")
            return None

    def _wait_for_deployment(self, deployment_id: str, timeout: int = 300) -> Optional[str]:
        """Wait for deployment to complete.

        Args:
            deployment_id: Deployment ID
            timeout: Maximum wait time in seconds

        Returns:
            Deployment URL or None
        """
        import time

        start_time = time.time()
        url = f"{self.base_url}/v13/deployments/{deployment_id}"

        while time.time() - start_time < timeout:
            try:
                response = requests.get(url, headers=self.headers)
                response.raise_for_status()
                deployment = response.json()

                status = deployment.get("readyState")
                if status == "READY":
                    return deployment.get("url")
                elif status in ["ERROR", "CANCELED"]:
                    return None

                time.sleep(10)  # Check every 10 seconds

            except Exception:
                return None

        return None

    def get_deployment_status(self, deployment_id: str) -> Optional[Dict]:
        """Get deployment status.

        Args:
            deployment_id: Deployment ID

        Returns:
            Deployment status dictionary
        """
        if not self.token:
            return None

        try:
            url = f"{self.base_url}/v13/deployments/{deployment_id}"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()

        except Exception as e:
            print(f"Error fetching deployment status: {e}")
            return None
