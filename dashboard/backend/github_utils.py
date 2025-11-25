"""
GitHub URL parsing and validation utilities
Handles repository URL extraction with comprehensive error handling and logging
"""

import re
import logging
from typing import Optional, Dict
from urllib.parse import urlparse

# Configure logging
logger = logging.getLogger(__name__)

class GitHubURLError(Exception):
    """Raised when GitHub URL parsing fails"""
    pass

def validate_github_url(url: str) -> bool:
    """
    Validate if a URL is a valid GitHub repository URL

    Args:
        url: URL to validate

    Returns:
        True if valid GitHub URL, False otherwise
    """
    if not url:
        return False

    # Check for GitHub domain
    if url.startswith('git@github.com:'):
        return True

    try:
        parsed = urlparse(url)
        if parsed.netloc != 'github.com':
            return False

        # Must have at least owner/repo in path
        path_parts = [p for p in parsed.path.split('/') if p]
        return len(path_parts) >= 2
    except:
        return False

def parse_github_url(url: str) -> Optional[Dict[str, str]]:
    """
    Parse a GitHub URL and extract owner, repo, and branch information.

    Supports formats:
    - https://github.com/owner/repo
    - https://github.com/owner/repo.git
    - https://github.com/owner/repo/tree/branch
    - git@github.com:owner/repo.git

    Args:
        url: GitHub repository URL

    Returns:
        Dict with owner, repo, branch, full_url

    Raises:
        GitHubURLError: If URL is invalid
    """
    if not url:
        logger.error("parse_github_url: Empty URL provided")
        raise GitHubURLError("GitHub URL cannot be empty")

    url = url.strip()
    logger.info(f"Parsing GitHub URL: {url}")

    # Handle git@ SSH format
    if url.startswith('git@github.com:'):
        logger.debug("Detected SSH format URL")
        match = re.match(r'git@github\.com:([^/]+)/(.+?)(?:\.git)?$', url)
        if match:
            owner, repo = match.groups()
            logger.info(f"Successfully parsed SSH URL: {owner}/{repo}")
            return {
                'owner': owner,
                'repo': repo,
                'branch': 'main',
                'full_url': f'https://github.com/{owner}/{repo}'
            }
        else:
            logger.error(f"Invalid SSH URL format: {url}")
            raise GitHubURLError(
                f"Invalid Git SSH URL format: {url}. "
                f"Expected format: git@github.com:owner/repo.git"
            )

    # Handle HTTPS format
    try:
        parsed = urlparse(url)
    except Exception as e:
        logger.error(f"URL parsing failed: {e}")
        raise GitHubURLError(f"Malformed URL: {url}")

    if not parsed.netloc:
        logger.error(f"No domain in URL: {url}")
        raise GitHubURLError(
            f"Invalid URL format: {url}. "
            f"Expected format: https://github.com/owner/repo"
        )

    if parsed.netloc != 'github.com':
        logger.error(f"Not a GitHub URL: {parsed.netloc}")
        raise GitHubURLError(
            f"Not a GitHub URL: {url}. "
            f"This tool only supports GitHub repositories. "
            f"Please provide a URL starting with https://github.com/"
        )

    # Extract path parts
    path_parts = [p for p in parsed.path.split('/') if p]

    if len(path_parts) < 2:
        logger.error(f"URL missing owner/repo: {url}, path_parts={path_parts}")
        raise GitHubURLError(
            f"Invalid GitHub URL: {url}. "
            f"URL must include owner and repository name. "
            f"Expected format: https://github.com/owner/repo"
        )

    owner = path_parts[0]
    repo = path_parts[1].replace('.git', '')

    # Validate owner and repo names
    if not owner or not repo:
        logger.error(f"Empty owner or repo: owner='{owner}', repo='{repo}'")
        raise GitHubURLError(
            f"Invalid GitHub URL: {url}. "
            f"Owner and repository name cannot be empty."
        )

    # Check for valid characters (GitHub allows alphanumeric, hyphen, underscore)
    if not re.match(r'^[a-zA-Z0-9_-]+$', owner):
        logger.error(f"Invalid owner name: {owner}")
        raise GitHubURLError(
            f"Invalid owner name: {owner}. "
            f"Owner must contain only letters, numbers, hyphens, and underscores."
        )

    if not re.match(r'^[a-zA-Z0-9_.-]+$', repo):
        logger.error(f"Invalid repo name: {repo}")
        raise GitHubURLError(
            f"Invalid repository name: {repo}. "
            f"Repository name must contain only letters, numbers, hyphens, periods, and underscores."
        )

    # Check for branch in URL
    branch = 'main'
    if len(path_parts) >= 4 and path_parts[2] == 'tree':
        branch = path_parts[3]
        logger.debug(f"Branch specified in URL: {branch}")

    result = {
        'owner': owner,
        'repo': repo,
        'branch': branch,
        'full_url': f'https://github.com/{owner}/{repo}'
    }

    logger.info(f"Successfully parsed GitHub URL: {owner}/{repo} (branch: {branch})")
    return result

def get_repo_default_url(owner: str, repo: str) -> str:
    """
    Generate default deployment URL for a GitHub repo.
    Common patterns for web apps.

    Args:
        owner: Repository owner
        repo: Repository name

    Returns:
        Default URL for the repository
    """
    # Common deployment patterns
    patterns = [
        f'https://{repo}.{owner}.com',  # Custom domain
        f'https://{owner}.github.io/{repo}',  # GitHub Pages
        f'http://localhost:3000',  # Local development
    ]

    # Return the most likely pattern (can be customized)
    # Default to localhost for security testing
    logger.debug(f"Generated default URL for {owner}/{repo}: {patterns[2]}")
    return patterns[2]

def extract_target_info_from_github(github_url: str) -> Dict[str, any]:
    """
    Extract target information from a GitHub URL.
    Returns a dict with name, url, github_repo, repo_owner, repo_name, github_branch.

    Args:
        github_url: GitHub repository URL

    Returns:
        Dict with target information

    Raises:
        GitHubURLError: If URL is invalid or parsing fails
    """
    logger.info(f"Extracting target info from: {github_url}")

    try:
        parsed = parse_github_url(github_url)
    except GitHubURLError:
        # Re-raise with original message
        raise
    except Exception as e:
        logger.error(f"Unexpected error parsing GitHub URL: {e}", exc_info=True)
        raise GitHubURLError(f"Failed to parse GitHub URL: {str(e)}")

    owner = parsed['owner']
    repo = parsed['repo']
    branch = parsed['branch']
    full_url = parsed['full_url']

    # Generate a descriptive name
    name = f"{owner}/{repo}"

    # Generate a default target URL
    target_url = get_repo_default_url(owner, repo)

    result = {
        'name': name,
        'url': target_url,
        'github_repo': full_url,
        'github_branch': branch,
        'repo_owner': owner,
        'repo_name': repo,
        'status': 'active'  # Default status
    }

    logger.info(f"Successfully extracted target info: {name}")
    logger.debug(f"Target info: {result}")

    return result


# Example URLs for testing
EXAMPLE_URLS = {
    'https://github.com/WebGoat/WebGoat': 'WebGoat/WebGoat',
    'https://github.com/juice-shop/juice-shop': 'juice-shop/juice-shop',
    'https://github.com/owner/repo.git': 'owner/repo',
    'https://github.com/owner/repo/tree/develop': 'owner/repo (branch: develop)',
    'git@github.com:owner/repo.git': 'owner/repo (SSH)',
}

if __name__ == "__main__":
    # Test the parser with example URLs
    logging.basicConfig(level=logging.DEBUG)

    print("Testing GitHub URL parser:\n")
    for url, expected in EXAMPLE_URLS.items():
        try:
            result = extract_target_info_from_github(url)
            print(f"✅ {url}")
            print(f"   → {result['name']} (branch: {result['github_branch']})")
        except GitHubURLError as e:
            print(f"❌ {url}")
            print(f"   → Error: {e}")
        print()
