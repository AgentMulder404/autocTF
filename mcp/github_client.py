"""
GitHub Client with Token Validation and Fail-Fast Errors
Validates token scopes and provides clear error messages
"""

from github import Github, GithubException
import github
import os
import base64
import logging
from dotenv import load_dotenv
from typing import Optional, Dict

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GitHubClientError(Exception):
    """Raised when GitHub client encounters an error"""
    pass

class GitHubClient:
    """GitHub client with validation and error handling"""

    def __init__(self):
        self.token = os.getenv("GITHUB_TOKEN")
        self.repo_name = os.getenv("GITHUB_REPO")

        # Validate configuration
        self._validate_config()

        # Initialize client
        if self.token and self.repo_name:
            auth = github.Auth.Token(self.token)
            self.g = Github(auth=auth)
            self._validate_connection()
        else:
            self.g = None

    def _validate_config(self):
        """Validate GitHub configuration"""
        if not self.token:
            raise GitHubClientError(
                "GITHUB_TOKEN not set in environment. "
                "Generate token at: https://github.com/settings/tokens"
            )

        if not self.repo_name:
            raise GitHubClientError(
                "GITHUB_REPO not set in environment. "
                "Format should be: owner/repository"
            )

        # Check if token is placeholder
        if self._is_placeholder(self.token):
            raise GitHubClientError(
                f"GITHUB_TOKEN appears to be a placeholder: {self.token[:20]}... "
                "Replace with real token from https://github.com/settings/tokens"
            )

        logger.info(f"✅ GitHub config loaded: {self.repo_name}")

    def _is_placeholder(self, value: str) -> bool:
        """Check if token is a placeholder"""
        if value.count('x') > len(value) * 0.5:
            return True
        placeholder_patterns = ['xxx', 'placeholder', 'example', 'your_token']
        return any(p in value.lower() for p in placeholder_patterns)

    def _validate_connection(self):
        """Validate GitHub connection and permissions"""
        try:
            # Test authentication
            user = self.g.get_user()
            logger.info(f"✅ Authenticated as: {user.login}")

            # Test repository access
            repo = self.g.get_repo(self.repo_name)
            logger.info(f"✅ Repository access: {repo.name}")

            # Check write permissions
            if not repo.permissions.push:
                raise GitHubClientError(
                    f"GitHub token lacks write permissions to {self.repo_name}. "
                    "Ensure token has 'repo' scope and you have push access."
                )

            logger.info("✅ Write permissions verified")

            # Check rate limit
            rate_limit = self.g.get_rate_limit()
            remaining = rate_limit.core.remaining
            if remaining < 100:
                logger.warning(f"⚠️  Low GitHub API rate limit: {remaining} requests remaining")
            else:
                logger.info(f"✅ API rate limit: {remaining}/{rate_limit.core.limit}")

        except GithubException as e:
            if e.status == 401:
                raise GitHubClientError(
                    "GitHub authentication failed (401). "
                    "Token may be invalid or expired. "
                    "Generate new token at: https://github.com/settings/tokens"
                )
            elif e.status == 404:
                raise GitHubClientError(
                    f"Repository not found: {self.repo_name}. "
                    "Check GITHUB_REPO format (owner/repository) and permissions."
                )
            elif e.status == 403:
                raise GitHubClientError(
                    "GitHub API access forbidden (403). "
                    "Check token scopes include 'repo' and 'workflow'."
                )
            else:
                raise GitHubClientError(f"GitHub API error: {e.data.get('message', str(e))}")

    def get_repo(self):
        """Get repository object"""
        if not self.g:
            raise GitHubClientError("GitHub client not initialized")

        try:
            return self.g.get_repo(self.repo_name)
        except GithubException as e:
            raise GitHubClientError(f"Failed to access repository: {e.data.get('message', str(e))}")

    def create_pr(
        self,
        title: str,
        body: str,
        branch: str,
        files: Dict[str, str],
        screenshots: list = None,
        dump_data: dict = None
    ) -> str:
        """
        Create a pull request with file changes

        Args:
            title: PR title
            body: PR description
            branch: Branch name for PR
            files: Dict of file paths to content
            screenshots: List of screenshot URLs (optional)
            dump_data: Database dump data (optional)

        Returns:
            PR URL

        Raises:
            GitHubClientError: If PR creation fails
        """
        if not self.g:
            raise GitHubClientError("GitHub client not initialized")

        try:
            repo = self.get_repo()

            # Enhance PR body with exploitation details
            enhanced_body = self._generate_enhanced_pr_body(body, screenshots, dump_data)

            logger.info(f"📝 Creating PR: {title}")

            # Get base branch
            try:
                base = repo.get_branch("master")
                base_name = "master"
            except:
                base = repo.get_branch("main")
                base_name = "main"

            logger.info(f"🌿 Base branch: {base_name}")

            # Create new branch
            try:
                repo.create_git_ref(ref=f"refs/heads/{branch}", sha=base.commit.sha)
                logger.info(f"✅ Created branch: {branch}")
            except GithubException as e:
                if e.status == 422:  # Branch already exists
                    logger.warning(f"⚠️  Branch {branch} already exists, using existing")
                else:
                    raise GitHubClientError(f"Failed to create branch: {e.data.get('message', str(e))}")

            # Upload files
            logger.info(f"📤 Uploading {len(files)} file(s)...")
            for path, content in files.items():
                try:
                    # Check if file exists
                    try:
                        f = repo.get_contents(path, ref=base_name)
                        # Update existing file
                        repo.update_file(
                            path,
                            f"[AutoCTF] Patch {path}",
                            content,
                            f.sha,
                            branch=branch
                        )
                        logger.info(f"  ✅ Updated: {path}")
                    except GithubException as e:
                        if e.status == 404:
                            # Create new file
                            repo.create_file(
                                path,
                                f"[AutoCTF] Add {path}",
                                content,
                                branch=branch
                            )
                            logger.info(f"  ✅ Created: {path}")
                        else:
                            raise
                except GithubException as e:
                    logger.error(f"  ❌ Failed to upload {path}: {e.data.get('message', str(e))}")
                    raise GitHubClientError(f"File upload failed for {path}")

            # Create pull request
            logger.info("📬 Creating pull request...")
            try:
                pr = repo.create_pull(
                    title=title,
                    body=enhanced_body,
                    head=branch,
                    base=base_name
                )

                pr_url = pr.html_url
                logger.info(f"✅ PR created: {pr_url}")

                return pr_url

            except GithubException as e:
                if e.status == 422:
                    error_msg = e.data.get('errors', [{}])[0].get('message', '')
                    if 'pull request already exists' in error_msg.lower():
                        logger.warning("⚠️  PR already exists for this branch")
                        # Try to find existing PR
                        prs = repo.get_pulls(state='open', head=f"{repo.owner.login}:{branch}")
                        for pr in prs:
                            return pr.html_url
                    raise GitHubClientError(f"PR creation failed: {error_msg}")
                else:
                    raise GitHubClientError(f"PR creation failed: {e.data.get('message', str(e))}")

        except GitHubClientError:
            raise
        except Exception as e:
            logger.error(f"❌ Unexpected error creating PR: {e}")
            raise GitHubClientError(f"Unexpected error: {str(e)}")

    def _generate_enhanced_pr_body(
        self,
        original_body: str,
        screenshots: list,
        dump_data: dict
    ) -> str:
        """Generate enhanced PR body with exploitation evidence"""
        body_parts = [
            "# 🎯 AutoCTF Security Patch",
            "",
            original_body,
            "",
            "---",
            "",
            "## 🔥 EXPLOITATION EVIDENCE",
            ""
        ]

        # Add dump summary if available
        if dump_data and dump_data.get('summary'):
            body_parts.extend([
                "### 💀 SQLi Exploitation Summary",
                "```",
                dump_data['summary'],
                "```",
                ""
            ])

        # Add database enumeration
        if dump_data and dump_data.get('databases'):
            body_parts.extend([
                "### 💾 Databases Compromised",
                ""
            ])
            for db in dump_data['databases']:
                body_parts.append(f"- ✅ `{db}` - **DUMPED**")
            body_parts.append("")

        # Add credentials if found
        if dump_data and dump_data.get('credentials'):
            body_parts.extend([
                "### 🔑 Credentials Extracted",
                "",
                f"⚠️ **{len(dump_data['credentials'])} credential entries found**",
                "",
                "<details>",
                "<summary>View Extracted Credentials (Click to expand)</summary>",
                "",
                "```"
            ])
            for cred in dump_data['credentials'][:5]:  # Limit to first 5
                body_parts.append(cred)
                body_parts.append("---")
            body_parts.extend([
                "```",
                "</details>",
                ""
            ])

        # Add screenshots
        if screenshots:
            body_parts.extend([
                "### 📸 Proof of Exploitation",
                "",
                "*Screenshots captured during exploitation:*",
                ""
            ])
            for i, screenshot_url in enumerate(screenshots, 1):
                if screenshot_url and screenshot_url.startswith("http"):
                    body_parts.append(f"![Exploitation Screenshot {i}]({screenshot_url})")
                else:
                    body_parts.append(f"- Screenshot {i}: `{screenshot_url}`")
            body_parts.append("")

        # Add remediation info
        body_parts.extend([
            "---",
            "",
            "## 🛡️ REMEDIATION",
            "",
            "### ⚡ IMMEDIATE ACTIONS REQUIRED:",
            "1. 🔍 **Review** - Carefully review all code changes",
            "2. 🧪 **Test** - Run your test suite",
            "3. 🔒 **Deploy** - Merge and deploy ASAP",
            "4. 🔑 **Rotate** - Change exposed credentials",
            "5. 📊 **Audit** - Check logs for exploitation signs",
            "",
            "---",
            "",
            "🤖 **Generated by AutoCTF** - Autonomous Pentesting Agent",
            ""
        ])

        return "\n".join(body_parts)


# Global client instance
_client = None

def get_client() -> GitHubClient:
    """Get or create global GitHub client"""
    global _client
    if _client is None:
        _client = GitHubClient()
    return _client


# Backward compatibility functions
def get_repo():
    """Get repository object (backward compatibility)"""
    client = get_client()
    return client.get_repo()


def create_pr(
    title: str,
    body: str,
    branch: str,
    files: dict,
    screenshots: list = None,
    dump_data: dict = None
) -> str:
    """Create PR (backward compatibility)"""
    client = get_client()
    return client.create_pr(title, body, branch, files, screenshots, dump_data)


# Validation on import - fail fast if misconfigured
try:
    # Only validate if being imported for actual use (not during diagnostic)
    import sys
    if 'diagnose' not in ' '.join(sys.argv).lower():
        _client = GitHubClient()
        logger.info("✅ GitHub client initialized successfully")
except GitHubClientError as e:
    logger.error(f"❌ GitHub client initialization failed: {e}")
    logger.error("   Fix GitHub configuration before running pentests")
    # Don't raise - allow import but fail later with clear error
except Exception as e:
    logger.warning(f"⚠️  GitHub client pre-validation skipped: {e}")
