# GitFlowAI — GitHub Workflow Automation Tool

A powerful, single-file Python utility to automate your entire Git/GitHub workflow from the command line.

This repository contains `gitflowapp.py`, a lightweight script that automates the common workflow of creating a repo on GitHub and pushing an existing local project to it.

## Features

- Create public or private repositories using the GitHub API
- Optionally initialize a local git repo, stage, commit and push code
- Configurable via environment variables, a `github_config.json` file, or CLI arguments
- JSON output mode for machine-readable responses
- Minimal dependencies (only `requests`)

## Requirements

- Python 3.6+
- Git installed and available in PATH
- `requests` Python package

Install the Python dependency:

```bash
pip install requests
```

## Quick Start

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

The repository includes two main commands (via `gitflowapp.py`): `create` and `push`.

Create a new repository (and push current directory):

PowerShell example (current directory):

```powershell
python create_github_repo.py create --name my-project
```

Create without pushing code:

```powershell
python gitflowapp.py create --name my-project --no-push
```

Create and push a specific path (Windows example):

```powershell
python gitflowapp.py create --name my-app --path "E:\Code\MyApp" --branch main
```

Get JSON output:

```powershell
python gitflowapp.py create --name my-app --json
```

Push an existing local directory to an already-created GitHub repository:

```powershell
python gitflowapp.py push --name existing-repo --path "E:\Code\Project"
```

## Command options (summary)

- `--name, -n`: Repository name (required for `create` and `push`)
- `--description, -d`: Repository description (create)
- `--private, -p`: Make repository private (create)
- `--no-push`: Create repo but do not push local code (create)
- `--path`: Local directory path (default: current directory)
- `--branch, -b`: Branch name to push (default: `main`)
- `--json`: Output machine-readable JSON

Consult the script's `--help` for the full list and precise CLI behavior:

```powershell
python gitflowapp.py --help
```

## How it works (high level)

- `create` calls the GitHub API to create a repository, initializes git locally if needed, commits files, and pushes to the new remote (unless `--no-push` is passed).
- `push` will push a local directory to an existing GitHub repository (useful if you already created the repo separately).

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

Start a new project and push current folder:

```powershell
mkdir my-project; cd my-project
echo "# My Project" > README.md
python ..\gitflowapp.py create --name my-project
```

Push an existing local project to an existing GitHub repo:

```powershell
cd E:\Code\ExistingProject
python ..\gitflowapp.py push --name existing-repo
```

## License

MIT — free to use and modify.


----

If you'd like, I can also:

- add a short example `github_config.json` file to the repository,
- create a small unit test harness for the script's helper functions (if present), or
- run the script with a dry-run mode (if you want me to add it).

Tell me which of those you'd like next.
