"""Build verification for quality assurance."""

import subprocess
import os
from pathlib import Path
from typing import Dict, Optional


class BuildVerifier:
    """Verifies build and tests pass after changes."""

    def __init__(self, dry_run: bool = False, project_root: Optional[Path] = None):
        """Initialize build verifier.

        Args:
            dry_run: If True, only simulate build verification
            project_root: Root directory of project to verify (defaults to cwd)
        """
        self.dry_run = dry_run
        self.project_root = project_root or Path.cwd()

    def verify(self) -> bool:
        """Run build verification.

        Returns:
            True if build passes, False otherwise
        """
        if self.dry_run:
            print("[DRY RUN] Would verify build and tests")
            return True

        try:
            # Try common build commands
            if self._has_file("package.json"):
                return self._verify_node_project()
            elif self._has_file("requirements.txt") or self._has_file("pyproject.toml"):
                return self._verify_python_project()
            elif self._has_file("Cargo.toml"):
                return self._verify_rust_project()
            elif self._has_file("go.mod"):
                return self._verify_go_project()
            else:
                # No recognized build system
                return True

        except Exception as e:
            print(f"Build verification error: {e}")
            return False

    def _verify_node_project(self) -> bool:
        """Verify Node.js project build.

        Returns:
            True if successful
        """
        # Determine npm command (Windows needs .cmd)
        import platform
        npm_cmd = "npm.cmd" if platform.system() == "Windows" else "npm"
        
        # Install dependencies if needed (with caching support)
        if not self._has_dir("node_modules"):
            print(f"\n[BUILD] Installing npm dependencies in {self.project_root}...")
            print("[BUILD] This may take a few minutes on first run...")
            
            # Use npm ci for faster, reproducible installs if package-lock.json exists
            if (self.project_root / "package-lock.json").exists():
                print("[BUILD] Using 'npm ci' (clean install with lockfile)")
                cmd = [npm_cmd, "ci", "--prefer-offline", "--no-audit"]
            else:
                print("[BUILD] Using 'npm install'")
                cmd = [npm_cmd, "install", "--prefer-offline", "--no-audit"]
            
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                shell=True  # Required on Windows for .cmd files
            )
            
            if result.returncode != 0:
                print(f"\n[ERROR] npm install failed!")
                print(f"STDOUT: {result.stdout}")
                print(f"STDERR: {result.stderr}")
                return False
            
            print("[BUILD] Dependencies installed successfully")
        else:
            print(f"[BUILD] node_modules already exists, skipping install")

        # Run build
        print(f"\n[BUILD] Running npm run build in {self.project_root}...")
        result = subprocess.run(
            [npm_cmd, "run", "build"],
            cwd=self.project_root,
            capture_output=True,
            text=True,
            shell=True  # Required on Windows
        )

        print(f"\n{'='*60}")
        print(f"[BUILD OUTPUT] Exit Code: {result.returncode}")
        print(f"{'='*60}")
        if result.stdout:
            print(f"STDOUT:\n{result.stdout}")
        if result.stderr:
            print(f"\nSTDERR:\n{result.stderr}")
        print(f"{'='*60}\n")

        if result.returncode != 0:
            return False

        # Run tests if test script exists
        package_json_path = self.project_root / "package.json"
        if package_json_path.exists():
            import json
            with open(package_json_path) as f:
                package = json.load(f)
                if "test" in package.get("scripts", {}):
                    print("[BUILD] Running tests...")
                    result = subprocess.run(
                        [npm_cmd, "test"],
                        cwd=self.project_root,
                        capture_output=True,
                        text=True,
                        shell=True
                    )
                    if result.returncode != 0:
                        print(f"[ERROR] Tests failed: {result.stderr}")
                        return False
                    print("[BUILD] Tests passed")
                    return True

        return True

    def _verify_python_project(self) -> bool:
        """Verify Python project.

        Returns:
            True if successful
        """
        # Run tests if pytest is available
        result = subprocess.run(
            ["pytest", "-v"],
            cwd=self.project_root,
            capture_output=True
        )

        # Consider success if no tests or tests pass
        return result.returncode in [0, 5]  # 5 = no tests collected

    def _verify_rust_project(self) -> bool:
        """Verify Rust project build.

        Returns:
            True if successful
        """
        result = subprocess.run(
            ["cargo", "build"],
            cwd=self.project_root,
            capture_output=True
        )

        if result.returncode != 0:
            return False

        # Run tests
        result = subprocess.run(
            ["cargo", "test"],
            cwd=self.project_root,
            capture_output=True
        )

        return result.returncode == 0

    def _verify_go_project(self) -> bool:
        """Verify Go project build.

        Returns:
            True if successful
        """
        result = subprocess.run(
            ["go", "build", "./..."],
            cwd=self.project_root,
            capture_output=True
        )

        if result.returncode != 0:
            return False

        # Run tests
        result = subprocess.run(
            ["go", "test", "./..."],
            cwd=self.project_root,
            capture_output=True
        )

        return result.returncode == 0

    def _has_file(self, filename: str) -> bool:
        """Check if file exists in project root.

        Args:
            filename: Name of file

        Returns:
            True if exists
        """
        return (self.project_root / filename).exists()

    def _has_dir(self, dirname: str) -> bool:
        """Check if directory exists in project root.

        Args:
            dirname: Name of directory

        Returns:
            True if exists
        """
        return (self.project_root / dirname).is_dir()
