#!/usr/bin/env python3
"""
Pre-commit hook for registering git commits in Asana tasks.
This hook scans commit messages for Asana task IDs and adds comments to those tasks.
"""

import os
import re
import sys
import subprocess
import argparse
import json
import requests
from typing import List, Optional, Tuple

# Asana API constants
ASANA_API_URL = "https://app.asana.com/api/1.0"


def get_asana_token() -> str:
    """Get Asana API token from environment or git config."""
    # First try environment variable
    token = os.environ.get("ASANA_API_TOKEN")
    if token:
        return token

    # Try git config
    try:
        token = subprocess.check_output(
            ["git", "config", "--get", "asana.token"],
            universal_newlines=True
        ).strip()
        if token:
            return token
    except subprocess.CalledProcessError:
        pass

    sys.stderr.write("Error: Asana API token not found.\n")
    sys.stderr.write("Set it using: git config --global asana.token YOUR_TOKEN\n")
    sys.stderr.write("Or set the ASANA_API_TOKEN environment variable.\n")
    sys.exit(1)


def extract_task_ids(commit_msg: str) -> List[str]:
    """Extract Asana task IDs from commit message.

    Looks for patterns like:
    - "Fixes #123456789012345"
    - "Related to #123456789012345"
    - "asana:123456789012345"
    """
    # Pattern for Asana task IDs (usually 16-digit numbers)
    patterns = [
        r'(?:fixes|closes|resolves|references|refs|re|see|addresses)\s+(?:asana:)?#?(\d{16})',
        r'asana[:/](\d{16})',
        r'#(\d{16})'
    ]

    task_ids = []
    for pattern in patterns:
        matches = re.finditer(pattern, commit_msg, re.IGNORECASE)
        for match in matches:
            task_id = match.group(1)
            if task_id not in task_ids:
                task_ids.append(task_id)

    return task_ids


def get_commit_info() -> Tuple[str, str, str]:
    """Get the current commit information."""
    # Get commit message
    commit_msg = subprocess.check_output(
        ["git", "log", "-1", "--pretty=%B"],
        universal_newlines=True
    ).strip()

    # Get commit hash
    commit_hash = subprocess.check_output(
        ["git", "log", "-1", "--pretty=%H"],
        universal_newlines=True
    ).strip()

    # Get repo URL
    try:
        repo_url = subprocess.check_output(
            ["git", "config", "--get", "remote.origin.url"],
            universal_newlines=True
        ).strip()
        # Clean up repo URL if it's using SSH format
        if repo_url.startswith("git@"):
            repo_url = repo_url.replace(":", "/").replace("git@", "https://")
            if repo_url.endswith(".git"):
                repo_url = repo_url[:-4]
    except subprocess.CalledProcessError:
        repo_url = "Not available"

    return commit_msg, commit_hash, repo_url


def add_comment_to_task(task_id: str, commit_hash: str, commit_msg: str, repo_url: str) -> bool:
    """Add a comment to an Asana task about the commit."""
    token = get_asana_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # Create the comment text
    comment_text = f"Git commit registered:\n\n"
    comment_text += f"**Commit:** {commit_hash[:8]}\n"
    comment_text += f"**Message:** {commit_msg}\n"

    if repo_url != "Not available":
        # Try to create a link to the commit if we have a GitHub or GitLab repo
        if "github.com" in repo_url or "gitlab.com" in repo_url:
            commit_url = f"{repo_url}/commit/{commit_hash}"
            comment_text += f"**Link:** [View commit]({commit_url})\n"
        else:
            comment_text += f"**Repository:** {repo_url}\n"

    # Add the comment to the task
    url = f"{ASANA_API_URL}/tasks/{task_id}/stories"
    data = {
        "data": {
            "text": comment_text
        }
    }

    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        if response.status_code == 201:  # 201 Created
            print(f"Successfully added comment to Asana task {task_id}")
            return True
        else:
            error_msg = response.json().get("errors", [{"message": "Unknown error"}])[0].get("message")
            sys.stderr.write(f"Error adding comment to task {task_id}: {error_msg}\n")
            return False
    except Exception as e:
        sys.stderr.write(f"Error communicating with Asana API: {str(e)}\n")
        return False


def main() -> int:
    """Main function to execute the hook."""
    parser = argparse.ArgumentParser(description="Register git commits in Asana tasks")
    parser.add_argument(
        "--commit-msg-file",
        help="Path to the commit message file (for pre-commit hook)"
    )
    args = parser.parse_args()

    # Get commit information
    if args.commit_msg_file and os.path.exists(args.commit_msg_file):
        # We're being called as a commit-msg hook
        with open(args.commit_msg_file, 'r') as f:
            commit_msg = f.read().strip()
        # We don't have the commit hash yet, so use a placeholder
        commit_hash = "current commit"
    else:
        # We're being called as a post-commit hook or manually
        commit_msg, commit_hash, repo_url = get_commit_info()

    # Extract Asana task IDs from the commit message
    task_ids = extract_task_ids(commit_msg)

    if not task_ids:
        print("No Asana task IDs found in commit message.")
        return 0

    # Get repository URL
    try:
        repo_url = subprocess.check_output(
            ["git", "config", "--get", "remote.origin.url"],
            universal_newlines=True
        ).strip()
    except subprocess.CalledProcessError:
        repo_url = "Not available"

    # Add comments to each task
    success = True
    for task_id in task_ids:
        if not add_comment_to_task(task_id, commit_hash, commit_msg, repo_url):
            success = False

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())