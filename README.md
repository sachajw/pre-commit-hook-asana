# Asana Git Commit Integration

A pre-commit hook that automatically registers git commits in Asana tasks. This hook scans commit messages for Asana task IDs and adds comments to those tasks with information about the commit.

## Features

- Automatically detects Asana task IDs in commit messages
- Adds comments to Asana tasks with commit information
- Includes links to the commit (for GitHub and GitLab repositories)
- Supports multiple task references in a single commit

## Installation

### Prerequisites

- Python 3.6+
- [pre-commit](https://pre-commit.com/) framework installed
- Asana Personal Access Token

### Setting up your Asana API Token

You need an Asana Personal Access Token to authenticate with the Asana API. You can obtain one from your Asana account settings.

Once you have your token, you can set it up in one of two ways:

1. Set it as an environment variable:

   ```shell
   export ASANA_API_TOKEN=your_token_here
   ```

2. Set it in your git config (recommended for development machines):

   ```shell
   git config --global asana.token your_token_here
   ```

### Installing the hook

1. Add the hook to your `.pre-commit-config.yaml` file:

```yaml
repos:
-   repo: https://github.com/yourusername/pre-commit-asana
    rev: v0.1.0  # Use the latest version
    hooks:
    -   id: register-asana-commits
```

2. Install the pre-commit hooks:

```bash
pre-commit install --hook-type post-commit
```

## Usage

Once installed, the hook will automatically run after each commit. To use it:

1. Include Asana task IDs in your commit messages using one of these formats:
   - `Fixes #1234567890123456`
   - `Resolves asana:1234567890123456`
   - `Related to #1234567890123456`
   - `See asana/1234567890123456`
   - Simply include `#1234567890123456` in your message

2. Make your commit as usual:

```bash
git commit -m "Add new feature #1234567890123456"
```

3. The hook will automatically run and add a comment to the specified Asana task(s) with information about your commit.

## Troubleshooting

If you encounter issues:

1. Ensure your Asana API token is correctly set
2. Check that you have internet access to reach the Asana API
3. Verify that the task IDs in your commit messages are valid

## Manual Execution

You can also run the hook manually:

```bash
asana_git_hook.py
```

This will process the most recent commit and update any referenced Asana tasks.

## License

MIT
