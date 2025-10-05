#!/usr/bin/env python3
"""
Simple GitHub Repository Manager
Create repos and push code to GitHub from the command line.

Usage:
    python create_github_repo.py create              # Create repo and push code
    python create_github_repo.py create --no-push    # Create repo only
    python create_github_repo.py push                # Push to existing repo
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


def run_git(command, cwd=None):
    """Run a git command and return success status."""
    try:
        subprocess.run(command, cwd=cwd, check=True, capture_output=True, text=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Git error: {e.stderr}")
        return False


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


def main():
    parser = argparse.ArgumentParser(description='Simple GitHub repository manager')
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
    
    args = parser.parse_args()
    config = load_config()
    token = get_token(config)
    
    result = None
    if args.command == 'create':
        result = cmd_create(args, config, token)
    elif args.command == 'push':
        result = cmd_push(args, config, token)
    
    if args.json and result:
        print(json.dumps(result, indent=2))
    else:
        print("\n✓ Done!")


if __name__ == '__main__':
    main()
