# GitFlowAI — GitHub Workflow Automation Tool

A powerful, single-file Python utility to automate your entire Git/GitHub workflow from the command line.

## Why GitFlowAI?

GitFlowAI streamlines your development workflow by automating repetitive Git and GitHub operations. Perfect for:

- **AI Agents & Automation**: Clean JSON output makes it ideal for integration with AI assistants, CI/CD pipelines, and automation scripts
- **Rapid Development**: Execute complete workflows (create repo → branch → commit → PR) in seconds
- **Solo Developers**: Simplify your workflow without complex Git commands
- **Team Collaboration**: Standardize repository creation and PR workflows across your team
- **Learning Git**: Clear, simple commands that abstract away Git complexity

Instead of remembering multiple Git commands and GitHub API calls, use simple, intuitive commands that handle everything for you.

## Features

- **Create repositories**: Create public or private repositories using the GitHub API
- **Push code**: Initialize local git repo, stage, commit and push code to GitHub
- **Commit changes**: Commit and push changes with custom messages
- **Create branches**: Create and push new branches for feature development
- **Open pull requests**: Create PRs directly from the command line
- **JSON output mode**: Machine-readable responses for AI/API integrations
- **Flexible configuration**: Use environment variables, config file, or CLI arguments
- **Minimal dependencies**: Only requires `requests` Python package

## Quick Start

```powershell
# 1. Install dependencies
pip install requests

# 2. Set your GitHub token
$env:GITHUB_TOKEN = "ghp_your_token_here"

# 3. Create a repo and push your code
python gitflowapp.py create --name my-project

# 4. Make changes and commit
python gitflowapp.py commit -m "Added new feature"

# 5. Create a feature branch
python gitflowapp.py branch -n awesome-feature

# 6. Open a pull request
python gitflowapp.py pr -t "Add awesome feature"
```

That's it! You've just automated your entire Git/GitHub workflow.

## Requirements

- Python 3.6+
- Git installed and available in PATH
- `requests` Python package

Install the Python dependency:

```bash
pip install requests
```

## Detailed Setup

1. Get a GitHub personal access token (classic) with the `repo` scope: [GitHub personal access tokens](https://github.com/settings/tokens)
2. Configure the token via environment variable or `github_config.json` (examples below).
3. Run the script to create and (optionally) push your code.

### Configure token (recommended)

PowerShell (temporary for session):

```powershell
$env:GITHUB_TOKEN = "ghp_your_token_here"
```

Linux/macOS (bash):

```bash
export GITHUB_TOKEN=ghp_your_token_here
```

### Option: `github_config.json`

You can create a `github_config.json` in the project directory to provide defaults and avoid passing arguments every time.

#### Setup Instructions

1. **Copy the example file**: The repository includes `github_config_example.json` as a template. Copy and rename it:
   
   ```powershell
   Copy-Item github_config_example.json github_config.json
   ```

2. **Edit your configuration**: Open `github_config.json` and add your GitHub personal access token and default settings:

   ```json
   {
     "github_token": "ghp_your_token_here",
     "repo_name": "my-project",
     "description": "My project description",
     "private": false,
     "push_code": true,
     "local_path": "",
     "branch": "main"
   }
   ```

3. **Configuration options explained**:
   - `github_token` (string, required): Your GitHub personal access token with `repo` scope
   - `repo_name` (string, optional): Default repository name (can be overridden with `--name`)
   - `description` (string, optional): Default repository description (can be overridden with `--description`)
   - `private` (boolean, optional): Make repositories private by default (can be overridden with `--private`)
   - `push_code` (boolean, optional): Whether to push code by default (can be overridden with `--no-push`)
   - `local_path` (string, optional): Default local path to push (empty string = current directory)
   - `branch` (string, optional): Default branch name (can be overridden with `--branch`)

4. **Security note**: The `github_config.json` file is automatically ignored by git (via `.gitignore`). Never commit your real token to version control. The example file is provided for reference only.

**Why use a config file?**

- Avoid typing your token or common settings repeatedly
- Set project-specific defaults
- Simplify commands: `python gitflowapp.py create` instead of `python gitflowapp.py create --name my-project --description "..." --private`

## Usage

GitFlowAI includes five main commands: `create`, `push`, `commit`, `branch`, and `pr`.

### Create a new repository

Create and push to a new GitHub repository:

```powershell
python gitflowapp.py create --name my-project
```

Create without pushing code:

```powershell
python gitflowapp.py create --name my-project --no-push
```

Create a private repository with description:

```powershell
python gitflowapp.py create --name my-app --description "My awesome app" --private
```

### Push to an existing repository

Push local code to an existing GitHub repository:

```powershell
python gitflowapp.py push --name existing-repo
```

### Commit and push changes

Commit all changes and push to current branch:

```powershell
python gitflowapp.py commit -m "Fixed authentication bug"
```

Commit to a specific branch:

```powershell
python gitflowapp.py commit -m "Add new feature" --branch feature-x
```

### Create a new branch

Create a new branch and push it to GitHub:

```powershell
python gitflowapp.py branch -n feature-auth
```

### Create a pull request

Create a PR from current branch to main:

```powershell
python gitflowapp.py pr -t "Add authentication" -b "This PR adds user authentication"
```

Create a PR to a different base branch:

```powershell
python gitflowapp.py pr -t "Bug fix" --base develop
```

### JSON output mode

Add `--json` flag before any command for machine-readable output:

```powershell
python gitflowapp.py --json commit -m "Update README"
python gitflowapp.py --json branch -n new-feature
python gitflowapp.py --json pr -t "New feature"
```

Example JSON output:

```json
{
  "action": "commit",
  "status": "success",
  "message": "Update README",
  "branch": "main",
  "repository": "GitFlowAI",
  "url": "https://github.com/username/GitFlowAI"
}
```

## Command options (summary)

### Global options

- `--json`: Output machine-readable JSON (use before command name)

### `create` command

- `--name, -n`: Repository name (required)
- `--description, -d`: Repository description
- `--private, -p`: Make repository private
- `--no-push`: Create repo but do not push local code
- `--path`: Local directory path (default: current directory)
- `--branch, -b`: Branch name (default: `main`)

### `push` command

- `--name, -n`: Repository name (required)
- `--path`: Local directory path (default: current directory)
- `--branch, -b`: Branch name (default: `main`)

### `commit` command

- `--message, -m`: Commit message (required)
- `--path`: Local directory path (default: current directory)
- `--branch, -b`: Branch to push to (default: current branch)

### `branch` command

- `--name, -n`: Branch name (required)
- `--path`: Local directory path (default: current directory)

### `pr` command

- `--title, -t`: Pull request title (default: formatted branch name)
- `--body, -b`: Pull request description
- `--base`: Base branch for PR (default: `main`)
- `--path`: Local directory path (default: current directory)

Consult the script's `--help` for the full list and precise CLI behavior:

```powershell
python gitflowapp.py --help
```

## How it works (high level)

- **`create`**: Calls the GitHub API to create a repository, initializes git locally if needed, commits files, and pushes to the new remote (unless `--no-push` is passed).
- **`push`**: Pushes a local directory to an existing GitHub repository (useful if you already created the repo separately).
- **`commit`**: Stages all changes, commits with your custom message, and pushes to the current or specified branch.
- **`branch`**: Creates a new branch locally, switches to it, and pushes it to GitHub.
- **`pr`**: Creates a pull request from the current branch to a base branch (default: main) using the GitHub API.

## Troubleshooting

- "GitHub token not found": set `GITHUB_TOKEN` env var or add to `github_config.json`.
- "Authentication failed": ensure the token has `repo` scope and is valid.
- "Repository already exists": choose a different name or delete the existing repo on GitHub.
- "Git is not installed": install Git and add it to your PATH.
- "Path does not exist": verify the `--path` argument is correct.

## Security

- Never commit your personal access token into the repository.
- Use environment variables for CI and automation instead of checked-in files.

## Examples

### Complete workflow example

```powershell
# 1. Create a new repository and push code
python gitflowapp.py create --name my-awesome-app --description "An awesome application"

# 2. Make some changes to your code, then commit
python gitflowapp.py commit -m "Added user authentication"

# 3. Create a new feature branch
python gitflowapp.py branch -n feature-payment

# 4. Make changes and commit to the feature branch
# ... edit your files ...
python gitflowapp.py commit -m "Implemented payment gateway"

# 5. Create a pull request
python gitflowapp.py pr -t "Add payment feature" -b "This PR adds Stripe payment integration"
```

### Using JSON mode for automation

```powershell
# Create repo and capture JSON output
$result = python gitflowapp.py --json create --name auto-deploy | ConvertFrom-Json
Write-Host "Repository created at: $($result.url)"

# Commit changes and parse result
$commit = python gitflowapp.py --json commit -m "Deploy v1.0" | ConvertFrom-Json
if ($commit.status -eq "success") {
    Write-Host "Successfully deployed to $($commit.branch)"
}
```

### Start a new project

```powershell
# Create project directory
mkdir my-project
cd my-project
echo "# My Project" > README.md

# Create repo and push
python ..\gitflowapp.py create --name my-project
```

### Push an existing project

```powershell
cd E:\Code\ExistingProject
python gitflowapp.py push --name existing-repo
```

## License

MIT — free to use and modify.


----

If you'd like, I can also:

- add a short example `github_config.json` file to the repository,
- create a small unit test harness for the script's helper functions (if present), or
- run the script with a dry-run mode (if you want me to add it).

Tell me which of those you'd like next.
