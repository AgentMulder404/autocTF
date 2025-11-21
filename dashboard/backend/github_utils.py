import re
from typing import Optional, Dict
from urllib.parse import urlparse

def parse_github_url(url: str) -> Optional[Dict[str, str]]:
    """
    Parse a GitHub URL and extract owner, repo, and branch information.

    Supports formats:
    - https://github.com/owner/repo
    - https://github.com/owner/repo.git
    - https://github.com/owner/repo/tree/branch
    - git@github.com:owner/repo.git
    """
    if not url:
        return None

    # Handle git@ SSH format
    if url.startswith('git@github.com:'):
        match = re.match(r'git@github\.com:([^/]+)/(.+?)(?:\.git)?$', url)
        if match:
            owner, repo = match.groups()
            return {
                'owner': owner,
                'repo': repo,
                'branch': 'main',
                'full_url': f'https://github.com/{owner}/{repo}'
            }

    # Handle HTTPS format
    parsed = urlparse(url)
    if parsed.netloc != 'github.com':
        return None

    # Extract path parts
    path_parts = [p for p in parsed.path.split('/') if p]

    if len(path_parts) < 2:
        return None

    owner = path_parts[0]
    repo = path_parts[1].replace('.git', '')

    # Check for branch in URL
    branch = 'main'
    if len(path_parts) >= 4 and path_parts[2] == 'tree':
        branch = path_parts[3]

    return {
        'owner': owner,
        'repo': repo,
        'branch': branch,
        'full_url': f'https://github.com/{owner}/{repo}'
    }

def get_repo_default_url(owner: str, repo: str) -> str:
    """
    Generate default deployment URL for a GitHub repo.
    Common patterns for web apps.
    """
    # Common deployment patterns
    patterns = [
        f'https://{repo}.{owner}.com',  # Custom domain
        f'https://{owner}.github.io/{repo}',  # GitHub Pages
        f'http://localhost:3000',  # Local development
    ]

    # Return the most likely pattern (can be customized)
    return patterns[2]  # Default to localhost for now

def extract_target_info_from_github(github_url: str) -> Dict[str, any]:
    """
    Extract target information from a GitHub URL.
    Returns a dict with name, url, github_repo, repo_owner, repo_name, github_branch.
    """
    parsed = parse_github_url(github_url)

    if not parsed:
        raise ValueError("Invalid GitHub URL format")

    owner = parsed['owner']
    repo = parsed['repo']
    branch = parsed['branch']
    full_url = parsed['full_url']

    # Generate a descriptive name
    name = f"{owner}/{repo}"

    # Generate a default target URL
    target_url = get_repo_default_url(owner, repo)

    return {
        'name': name,
        'url': target_url,
        'github_repo': full_url,
        'github_branch': branch,
        'repo_owner': owner,
        'repo_name': repo
    }
