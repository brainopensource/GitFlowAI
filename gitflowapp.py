#!/usr/bin/env python3
"""
GitFlowAI - GitHub Workflow Automation Tool
Automate your entire Git/GitHub workflow from the command line.

Usage:
    python gitflowapp.py create --name my-repo       # Create repo and push code
    python gitflowapp.py commit -m "Fix bug"         # Commit and push changes
    python gitflowapp.py branch -n feature-x         # Create and push new branch
    python gitflowapp.py pr -t "New feature"         # Create pull request
"""

import requests
import json
import sys
import subprocess
import os
import argparse


def load_config(path='github_config.json'):
    """Load config file, return empty dict if not found."""
    try:
        with open(path) as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def get_token(config):
    """Get GitHub token from env or config."""
    token = os.environ.get('GITHUB_TOKEN') or config.get('github_token')
    if not token:
        print("Error: GitHub token not found. Set GITHUB_TOKEN env var or add to config.")
        sys.exit(1)
    return token


def run_git(command, cwd=None, capture=True):
    """Run a git command and return success status."""
    try:
        result = subprocess.run(command, cwd=cwd, check=True, capture_output=capture, text=True)
        return result if capture else True
    except subprocess.CalledProcessError as e:
        if capture:
            print(f"Git error: {e.stderr}")
        return False


def get_current_branch(local_path=None):
    """Get the current git branch."""
    result = subprocess.run(['git', 'branch', '--show-current'], 
                          cwd=local_path, capture_output=True, text=True)
    if result.returncode == 0:
        return result.stdout.strip()
    return None


def get_repo_info(local_path=None):
    """Get repository name and owner from git remote."""
    result = subprocess.run(['git', 'remote', 'get-url', 'origin'], 
                          cwd=local_path, capture_output=True, text=True)
    if result.returncode != 0:
        return None, None
    
    # Parse URL like https://github.com/owner/repo.git or git@github.com:owner/repo.git
    url = result.stdout.strip()
    if 'github.com' in url:
        parts = url.replace('.git', '').replace(':', '/').split('/')
        if len(parts) >= 2:
            return parts[-2], parts[-1]  # owner, repo
    return None, None


def create_repo(token, name, description='', private=False, auto_init=True):
    """Create a GitHub repository."""
    response = requests.post(
        'https://api.github.com/user/repos',
        headers={'Authorization': f'token {token}', 'Accept': 'application/vnd.github.v3+json'},
        json={'name': name, 'description': description, 'private': private, 'auto_init': auto_init}
    )
    
    if response.status_code == 201:
        return response.json()
    elif response.status_code == 422:
        print("Error: Repository already exists or name is invalid")
    elif response.status_code == 401:
        print("Error: Authentication failed. Check your token.")
    else:
        print(f"Error: Failed to create repository (HTTP {response.status_code})")
    sys.exit(1)


def push_code(local_path, repo_url, branch='main', quiet=False):
    """Initialize git repo and push to GitHub."""
    if not os.path.exists(local_path):
        if not quiet:
            print(f"Error: Path '{local_path}' does not exist")
        return False
    
    if not quiet:
        print(f"\nInitializing git in: {local_path}")
    
    # Init repo if needed
    if not os.path.exists(os.path.join(local_path, '.git')):
        if not run_git(['git', 'init'], local_path):
            return False
        if not quiet:
            print("✓ Git initialized")
    
    # Stage and commit
    if not quiet:
        print("Adding files...")
    if not run_git(['git', 'add', '.'], local_path):
        return False
    
    # Check if there's anything to commit
    result = subprocess.run(['git', 'status', '--porcelain'], cwd=local_path, 
                          capture_output=True, text=True)
    if result.stdout.strip():
        if not quiet:
            print("Committing...")
        if not run_git(['git', 'commit', '-m', 'Initial commit'], local_path):
            return False
    
    # Rename branch if needed
    result = subprocess.run(['git', 'branch', '--show-current'], cwd=local_path,
                          capture_output=True, text=True)
    if result.returncode == 0 and result.stdout.strip() and result.stdout.strip() != branch:
        run_git(['git', 'branch', '-M', branch], local_path)
    
    # Add/update remote
    subprocess.run(['git', 'remote', 'remove', 'origin'], cwd=local_path, 
                  stderr=subprocess.DEVNULL)
    if not run_git(['git', 'remote', 'add', 'origin', repo_url], local_path):
        return False
    
    # Push
    if not quiet:
        print(f"Pushing to GitHub...")
    if not run_git(['git', 'push', '-u', 'origin', branch], local_path):
        return False
    
    if not quiet:
        print("✓ Code pushed successfully!")
    return True


def cmd_create(args, config, token):
    """Handle 'create' command."""
    repo_name = args.name or config.get('repo_name')
    if not repo_name:
        print("Error: Repository name required (use --name or set in config)")
        sys.exit(1)
    
    description = args.description or config.get('description', '')
    private = args.private or config.get('private', False)
    should_push = not args.no_push and config.get('push_code', True)
    
    # Create repo
    if not args.json:
        print(f"Creating repository: {repo_name}")
    repo_data = create_repo(token, repo_name, description, private, auto_init=not should_push)
    
    result = {
        'action': 'create',
        'status': 'created',
        'repository': repo_name,
        'url': repo_data['html_url'],
        'private': private
    }
    
    if not args.json:
        print(f"✓ Repository created: {repo_data['html_url']}")
    
    # Push code if requested
    if should_push:
        local_path = args.path or config.get('local_path') or os.getcwd()
        branch = args.branch or config.get('branch', 'main')
        auth_url = repo_data['clone_url'].replace('https://', f'https://{token}@')
        
        result['push'] = True
        result['branch'] = branch
        result['local_path'] = local_path
        
        if push_code(local_path, auth_url, branch, quiet=args.json):
            result['push_status'] = 'success'
        else:
            result['push_status'] = 'failed'
            if args.json:
                print(json.dumps(result, indent=2))
            else:
                print("\n⚠ Repository created but push failed")
            sys.exit(1)
    
    return result


def cmd_push(args, config, token):
    """Handle 'push' command."""
    repo_name = args.name or config.get('repo_name')
    if not repo_name:
        print("Error: Repository name required (use --name or set in config)")
        sys.exit(1)
    
    # Get username
    response = requests.get('https://api.github.com/user',
                          headers={'Authorization': f'token {token}'})
    if response.status_code != 200:
        print("Error: Failed to get user info")
        sys.exit(1)
    
    username = response.json()['login']
    local_path = args.path or config.get('local_path') or os.getcwd()
    branch = args.branch or config.get('branch', 'main')
    
    repo_url = f"https://{token}@github.com/{username}/{repo_name}.git"
    
    result = {
        'action': 'push',
        'repository': repo_name,
        'branch': branch,
        'local_path': local_path,
        'url': f"https://github.com/{username}/{repo_name}"
    }
    
    if push_code(local_path, repo_url, branch, quiet=args.json):
        result['status'] = 'success'
        if not args.json:
            print(f"\n✓ View at: https://github.com/{username}/{repo_name}")
    else:
        result['status'] = 'failed'
        if args.json:
            print(json.dumps(result, indent=2))
        sys.exit(1)
    
    return result


def cmd_commit(args, config, token):
    """Handle 'commit' command - commit and push changes."""
    local_path = args.path or config.get('local_path') or os.getcwd()
    message = args.message or config.get('commit_message', 'Update')
    branch = args.branch or get_current_branch(local_path) or 'main'
    
    if not os.path.exists(os.path.join(local_path, '.git')):
        if not args.json:
            print("Error: Not a git repository. Run 'create' or 'push' first.")
        result = {'action': 'commit', 'status': 'failed', 'error': 'not_a_git_repo'}
        if args.json:
            print(json.dumps(result, indent=2))
        sys.exit(1)
    
    owner, repo_name = get_repo_info(local_path)
    
    if not args.json:
        print(f"Committing changes in: {local_path}")
        print(f"Branch: {branch}")
    
    # Stage all changes
    if not run_git(['git', 'add', '.'], local_path):
        result = {'action': 'commit', 'status': 'failed', 'error': 'git_add_failed'}
        if args.json:
            print(json.dumps(result, indent=2))
        sys.exit(1)
    
    # Check if there are changes to commit
    status_result = subprocess.run(['git', 'status', '--porcelain'], 
                                  cwd=local_path, capture_output=True, text=True)
    
    if not status_result.stdout.strip():
        if not args.json:
            print("✓ No changes to commit")
        result = {'action': 'commit', 'status': 'no_changes', 'branch': branch}
        if args.json:
            print(json.dumps(result, indent=2))
        return result
    
    # Commit
    if not args.json:
        print(f"Committing with message: '{message}'")
    if not run_git(['git', 'commit', '-m', message], local_path):
        result = {'action': 'commit', 'status': 'failed', 'error': 'git_commit_failed'}
        if args.json:
            print(json.dumps(result, indent=2))
        sys.exit(1)
    
    # Push
    if not args.json:
        print("Pushing to GitHub...")
    if not run_git(['git', 'push', 'origin', branch], local_path):
        result = {'action': 'commit', 'status': 'failed', 'error': 'git_push_failed'}
        if args.json:
            print(json.dumps(result, indent=2))
        sys.exit(1)
    
    result = {
        'action': 'commit',
        'status': 'success',
        'message': message,
        'branch': branch,
        'local_path': local_path
    }
    
    if owner and repo_name:
        result['repository'] = repo_name
        result['url'] = f"https://github.com/{owner}/{repo_name}"
    
    if not args.json:
        print("✓ Changes committed and pushed!")
        if owner and repo_name:
            print(f"✓ View at: https://github.com/{owner}/{repo_name}")
    
    return result


def cmd_branch(args, config, token):
    """Handle 'branch' command - create and push a new branch."""
    local_path = args.path or config.get('local_path') or os.getcwd()
    branch_name = args.name
    
    if not branch_name:
        if not args.json:
            print("Error: Branch name required (use --name or -n)")
        result = {'action': 'branch', 'status': 'failed', 'error': 'branch_name_required'}
        if args.json:
            print(json.dumps(result, indent=2))
        sys.exit(1)
    
    if not os.path.exists(os.path.join(local_path, '.git')):
        if not args.json:
            print("Error: Not a git repository. Run 'create' or 'push' first.")
        result = {'action': 'branch', 'status': 'failed', 'error': 'not_a_git_repo'}
        if args.json:
            print(json.dumps(result, indent=2))
        sys.exit(1)
    
    owner, repo_name = get_repo_info(local_path)
    current_branch = get_current_branch(local_path)
    
    if not args.json:
        print(f"Creating branch: {branch_name}")
        print(f"From: {current_branch}")
    
    # Create branch
    if not run_git(['git', 'checkout', '-b', branch_name], local_path):
        # Branch might already exist, try to switch to it
        if not run_git(['git', 'checkout', branch_name], local_path):
            result = {'action': 'branch', 'status': 'failed', 'error': 'git_checkout_failed'}
            if args.json:
                print(json.dumps(result, indent=2))
            sys.exit(1)
        if not args.json:
            print(f"✓ Switched to existing branch: {branch_name}")
    else:
        if not args.json:
            print(f"✓ Branch created: {branch_name}")
    
    # Push branch to remote
    if not args.json:
        print("Pushing branch to GitHub...")
    if not run_git(['git', 'push', '-u', 'origin', branch_name], local_path):
        result = {'action': 'branch', 'status': 'failed', 'error': 'git_push_failed'}
        if args.json:
            print(json.dumps(result, indent=2))
        sys.exit(1)
    
    result = {
        'action': 'branch',
        'status': 'success',
        'branch': branch_name,
        'previous_branch': current_branch,
        'local_path': local_path
    }
    
    if owner and repo_name:
        result['repository'] = repo_name
        result['url'] = f"https://github.com/{owner}/{repo_name}/tree/{branch_name}"
    
    if not args.json:
        print(f"✓ Branch pushed to GitHub!")
        if owner and repo_name:
            print(f"✓ View at: https://github.com/{owner}/{repo_name}/tree/{branch_name}")
    
    return result


def cmd_pr(args, config, token):
    """Handle 'pr' command - create a pull request."""
    local_path = args.path or config.get('local_path') or os.getcwd()
    title = args.title
    body = args.body or ''
    base = args.base or 'main'
    
    if not os.path.exists(os.path.join(local_path, '.git')):
        if not args.json:
            print("Error: Not a git repository. Run 'create' or 'push' first.")
        result = {'action': 'pr', 'status': 'failed', 'error': 'not_a_git_repo'}
        if args.json:
            print(json.dumps(result, indent=2))
        sys.exit(1)
    
    owner, repo_name = get_repo_info(local_path)
    current_branch = get_current_branch(local_path)
    
    if not owner or not repo_name:
        if not args.json:
            print("Error: Could not determine repository info from git remote")
        result = {'action': 'pr', 'status': 'failed', 'error': 'no_remote_info'}
        if args.json:
            print(json.dumps(result, indent=2))
        sys.exit(1)
    
    if not current_branch or current_branch == base:
        if not args.json:
            print(f"Error: Cannot create PR from {base} branch. Switch to a feature branch first.")
        result = {'action': 'pr', 'status': 'failed', 'error': 'invalid_branch'}
        if args.json:
            print(json.dumps(result, indent=2))
        sys.exit(1)
    
    # Use branch name as title if not provided
    if not title:
        title = current_branch.replace('-', ' ').replace('_', ' ').title()
    
    if not args.json:
        print(f"Creating pull request: {title}")
        print(f"From: {current_branch} → To: {base}")
    
    # Create PR via GitHub API
    response = requests.post(
        f'https://api.github.com/repos/{owner}/{repo_name}/pulls',
        headers={
            'Authorization': f'token {token}',
            'Accept': 'application/vnd.github.v3+json'
        },
        json={
            'title': title,
            'body': body,
            'head': current_branch,
            'base': base
        }
    )
    
    if response.status_code == 201:
        pr_data = response.json()
        result = {
            'action': 'pr',
            'status': 'success',
            'title': title,
            'head': current_branch,
            'base': base,
            'pr_number': pr_data['number'],
            'pr_url': pr_data['html_url'],
            'repository': repo_name
        }
        
        if not args.json:
            print(f"✓ Pull request created: #{pr_data['number']}")
            print(f"✓ View at: {pr_data['html_url']}")
        
        return result
    else:
        error_msg = response.json().get('message', 'Unknown error')
        if not args.json:
            print(f"Error: Failed to create PR - {error_msg}")
        result = {
            'action': 'pr',
            'status': 'failed',
            'error': error_msg,
            'http_status': response.status_code
        }
        if args.json:
            print(json.dumps(result, indent=2))
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description='GitFlowAI - GitHub workflow automation tool')
    parser.add_argument('--json', action='store_true', help='Output result as JSON')
    subparsers = parser.add_subparsers(dest='command', required=True)
    
    # Create command
    create = subparsers.add_parser('create', help='Create a new repository')
    create.add_argument('--name', '-n', help='Repository name')
    create.add_argument('--description', '-d', help='Repository description')
    create.add_argument('--private', '-p', action='store_true', help='Make private')
    create.add_argument('--no-push', action='store_true', help='Do not push code')
    create.add_argument('--path', help='Local code path (default: current dir)')
    create.add_argument('--branch', '-b', help='Branch name (default: main)')
    
    # Push command
    push = subparsers.add_parser('push', help='Push code to existing repository')
    push.add_argument('--name', '-n', help='Repository name')
    push.add_argument('--path', help='Local code path (default: current dir)')
    push.add_argument('--branch', '-b', help='Branch name (default: main)')
    
    # Commit command
    commit = subparsers.add_parser('commit', help='Commit and push changes')
    commit.add_argument('--message', '-m', required=True, help='Commit message')
    commit.add_argument('--path', help='Local code path (default: current dir)')
    commit.add_argument('--branch', '-b', help='Branch to push to (default: current branch)')
    
    # Branch command
    branch = subparsers.add_parser('branch', help='Create and push a new branch')
    branch.add_argument('--name', '-n', required=True, help='Branch name')
    branch.add_argument('--path', help='Local code path (default: current dir)')
    
    # PR command
    pr = subparsers.add_parser('pr', help='Create a pull request')
    pr.add_argument('--title', '-t', help='PR title (default: branch name)')
    pr.add_argument('--body', '-b', help='PR description/body')
    pr.add_argument('--base', help='Base branch (default: main)')
    pr.add_argument('--path', help='Local code path (default: current dir)')
    
    args = parser.parse_args()
    config = load_config()
    token = get_token(config)
    
    result = None
    if args.command == 'create':
        result = cmd_create(args, config, token)
    elif args.command == 'push':
        result = cmd_push(args, config, token)
    elif args.command == 'commit':
        result = cmd_commit(args, config, token)
    elif args.command == 'branch':
        result = cmd_branch(args, config, token)
    elif args.command == 'pr':
        result = cmd_pr(args, config, token)
    
    if args.json and result:
        print(json.dumps(result, indent=2))
    elif not args.json:
        print("\n✓ Done!")


if __name__ == '__main__':
    main()
