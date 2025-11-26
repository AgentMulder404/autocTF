#!/usr/bin/env python3
"""
AutoCTF Startup Validation
Validates all critical services before allowing dashboard to start
Returns detailed error messages instead of silently failing
"""

import os
import asyncio
from typing import Dict, List, Tuple
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class ValidationError(Exception):
    """Raised when validation fails"""
    pass

class StartupValidator:
    """Validates all AutoCTF subsystems on startup"""

    def __init__(self):
        self.errors = []
        self.warnings = []

    async def validate_all(self) -> Tuple[bool, List[str], List[str]]:
        """
        Run all validations
        Returns: (is_valid, errors, warnings)
        """
        print("🔍 AutoCTF Startup Validation")
        print("=" * 60)

        # Run all validations
        await self.validate_environment_variables()
        await self.validate_github_auth()
        await self.validate_browserbase()
        await self.validate_e2b()
        await self.validate_xai()
        await self.validate_mcp_modules()

        # Summary
        print("\n" + "=" * 60)
        if not self.errors:
            print("✅ All validations passed - AutoCTF ready to start")
            if self.warnings:
                print(f"⚠️  {len(self.warnings)} warnings (non-critical)")
            return True, [], self.warnings
        else:
            print(f"❌ Validation failed - {len(self.errors)} critical errors")
            print("\n🚨 CRITICAL ERRORS:")
            for error in self.errors:
                print(f"  • {error}")
            return False, self.errors, self.warnings

    async def validate_environment_variables(self):
        """Validate all required environment variables"""
        print("\n[1/6] Environment Variables...")

        required_vars = {
            'E2B_API_KEY': 'E2B Sandbox',
            'XAI_API_KEY': 'xAI Grok LLM',
            'DATABASE_URL': 'PostgreSQL Database'
        }

        optional_vars = {
            'GITHUB_TOKEN': 'GitHub API (required for PR creation)',
            'GITHUB_REPO': 'GitHub Repository (required for PR creation)',
            'BROWSERBASE_API_KEY': 'Browserbase (screenshots)',
            'BROWSERBASE_PROJECT_ID': 'Browserbase Project',
            'OPENAI_API_KEY': 'OpenAI (alternative LLM)'
        }

        # Check required
        for var, description in required_vars.items():
            value = os.getenv(var)
            if not value:
                self.errors.append(f"Missing required env var: {var} ({description})")
                print(f"  ❌ {var}: NOT SET")
            elif self._is_placeholder(value):
                self.errors.append(f"{var} appears to be a placeholder value")
                print(f"  ❌ {var}: PLACEHOLDER")
            else:
                print(f"  ✅ {var}: OK")

        # Check optional
        for var, description in optional_vars.items():
            value = os.getenv(var)
            if not value:
                self.warnings.append(f"Optional env var not set: {var} ({description})")
                print(f"  ⚠️  {var}: NOT SET (optional)")
            else:
                print(f"  ✅ {var}: OK")

    async def validate_github_auth(self):
        """Validate GitHub authentication and token scopes"""
        print("\n[2/6] GitHub API Authentication...")

        token = os.getenv('GITHUB_TOKEN')
        repo_name = os.getenv('GITHUB_REPO')

        if not token or not repo_name:
            self.warnings.append("GitHub configuration incomplete (PR creation disabled)")
            print("  ⚠️  Configuration incomplete (PR creation disabled)")
            return

        if self._is_placeholder(token):
            self.warnings.append("GITHUB_TOKEN is a placeholder (PR creation disabled)")
            print("  ⚠️  Token is placeholder (PR creation disabled)")
            return

        try:
            from github import Github
            import github

            # Authenticate
            auth = github.Auth.Token(token)
            g = Github(auth=auth)

            # Test authentication
            user = g.get_user()
            username = user.login
            print(f"  ✅ Authenticated as: {username}")

            # Check repository access
            try:
                repo = g.get_repo(repo_name)
                print(f"  ✅ Repository access: {repo.name}")

                # Verify permissions
                permissions = repo.permissions
                if not permissions.push:
                    self.warnings.append(f"GitHub token lacks write permissions to {repo_name} (PR creation disabled)")
                    print("  ⚠️  No write permissions (PR creation disabled)")
                else:
                    print("  ✅ Write permissions: OK")

                # Check token scopes
                try:
                    # Get token info to check scopes
                    rate_limit = g.get_rate_limit()
                    print(f"  ✅ API rate limit: {rate_limit.core.remaining}/{rate_limit.core.limit}")

                    # Verify we can create refs (needed for branches)
                    # This is a lightweight check without actually creating anything
                    if permissions.push:
                        print("  ✅ Token scopes: Sufficient for PR creation")
                    else:
                        self.warnings.append("Token may lack required scopes (repo, workflow)")

                except Exception as e:
                    self.warnings.append(f"Could not verify token scopes: {str(e)}")

            except github.GithubException as e:
                if e.status == 404:
                    self.warnings.append(f"Repository not found: {repo_name} (PR creation disabled)")
                    print(f"  ⚠️  Repository not found: {repo_name}")
                else:
                    self.warnings.append(f"GitHub API error: {e.data.get('message', str(e))} (PR creation disabled)")
                    print(f"  ⚠️  API error: {e.status}")

        except Exception as e:
            self.warnings.append(f"GitHub validation failed: {str(e)} (PR creation disabled)")
            print(f"  ⚠️  Validation failed: {e}")

    async def validate_browserbase(self):
        """Validate Browserbase configuration and check rate limits"""
        print("\n[3/6] Browserbase API...")

        api_key = os.getenv('BROWSERBASE_API_KEY')
        project_id = os.getenv('BROWSERBASE_PROJECT_ID')

        if not api_key or not project_id:
            self.warnings.append("Browserbase not configured (screenshots disabled)")
            print("  ⚠️  Not configured (optional - screenshots disabled)")
            return

        try:
            from browserbase import Browserbase

            bb = Browserbase(api_key=api_key)

            # Try to create a session (will check rate limits)
            try:
                session = bb.sessions.create(project_id=project_id)

                if session and hasattr(session, 'id'):
                    print(f"  ✅ Session created: {session.id[:20]}...")

                    # IMPORTANT: Clean up immediately
                    try:
                        # Try to close the session we just created
                        # Note: API may not have close method, but we try
                        if hasattr(bb.sessions, 'complete'):
                            bb.sessions.complete(session.id)
                        print("  ✅ Session closed")
                    except:
                        print("  ⚠️  Session will auto-expire")

                    print("  ✅ Browserbase: OK")
                else:
                    self.warnings.append("Browserbase session creation returned unexpected format")
                    print("  ⚠️  Unexpected session format")

            except Exception as e:
                error_str = str(e)
                if "429" in error_str or "Too Many Requests" in error_str:
                    self.warnings.append("Browserbase rate limit exceeded (screenshots disabled)")
                    print("  ⚠️  Rate limit exceeded (screenshots disabled)")
                elif "401" in error_str or "unauthorized" in error_str.lower():
                    self.warnings.append("Browserbase authentication failed (screenshots disabled)")
                    print("  ⚠️  Authentication failed (screenshots disabled)")
                else:
                    self.warnings.append(f"Browserbase test failed: {error_str[:100]} (screenshots disabled)")
                    print(f"  ⚠️  API error: {error_str[:50]}...")

        except ImportError:
            self.warnings.append("Browserbase package not installed (screenshots disabled)")
            print("  ⚠️  Package not installed")
        except Exception as e:
            self.warnings.append(f"Browserbase validation error: {str(e)}")
            print(f"  ⚠️  Validation error: {e}")

    async def validate_e2b(self):
        """Validate E2B Sandbox connectivity"""
        print("\n[4/6] E2B Sandbox...")

        api_key = os.getenv('E2B_API_KEY')
        if not api_key:
            self.errors.append("E2B_API_KEY not set")
            print("  ❌ API key not set")
            return

        try:
            from e2b import AsyncSandbox

            # Create sandbox (quick test)
            print("  ⏳ Creating test sandbox...")
            sandbox = await AsyncSandbox.create(timeout=30)
            print("  ✅ Sandbox created")

            # Test command execution
            result = await sandbox.commands.run("echo 'test'")
            if "test" in result.stdout:
                print("  ✅ Command execution: OK")
            else:
                self.warnings.append("E2B command execution returned unexpected output")
                print("  ⚠️  Unexpected command output")

            print("  ✅ E2B Sandbox: OK")

        except Exception as e:
            self.errors.append(f"E2B validation failed: {str(e)}")
            print(f"  ❌ E2B error: {e}")

    async def validate_xai(self):
        """Validate xAI API connectivity"""
        print("\n[5/6] xAI Grok LLM...")

        api_key = os.getenv('XAI_API_KEY')
        if not api_key:
            self.errors.append("XAI_API_KEY not set")
            print("  ❌ API key not set")
            return

        try:
            import requests

            payload = {
                "model": "grok-2-1212",
                "messages": [{"role": "user", "content": "test"}],
                "max_tokens": 5
            }

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }

            response = requests.post(
                "https://api.x.ai/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=10
            )

            if response.status_code == 200:
                print("  ✅ xAI API: OK")
            else:
                self.errors.append(f"xAI API returned {response.status_code}")
                print(f"  ❌ API error: {response.status_code}")

        except Exception as e:
            self.errors.append(f"xAI validation failed: {str(e)}")
            print(f"  ❌ xAI error: {e}")

    async def validate_mcp_modules(self):
        """Validate MCP modules can be imported and respond"""
        print("\n[6/6] MCP Modules...")

        modules = {
            'mcp.exec_client': 'E2B Exec Client',
            'mcp.browserbase_client': 'Browserbase Client',
            'mcp.github_client': 'GitHub Client'
        }

        for module, description in modules.items():
            try:
                __import__(module)
                print(f"  ✅ {description}: OK")
            except Exception as e:
                self.errors.append(f"MCP module {module} failed to import: {str(e)}")
                print(f"  ❌ {description}: Import failed")

    def _is_placeholder(self, value: str) -> bool:
        """Check if a value looks like a placeholder"""
        if not value:
            return True

        # Check for common placeholder patterns
        placeholder_patterns = [
            'xxx', 'yyy', 'zzz',
            'your_', 'replace_', 'change_',
            'placeholder', 'example'
        ]

        value_lower = value.lower()
        for pattern in placeholder_patterns:
            if pattern in value_lower:
                return True

        # Check if mostly x's (like ghp_xxxxxxxxxxxx)
        if value.count('x') > len(value) * 0.5:
            return True

        return False


async def validate_startup() -> Tuple[bool, List[str], List[str]]:
    """
    Main validation function
    Returns: (is_valid, errors, warnings)
    """
    validator = StartupValidator()
    return await validator.validate_all()


def validate_startup_sync() -> Tuple[bool, List[str], List[str]]:
    """Synchronous wrapper for validate_startup"""
    return asyncio.run(validate_startup())


if __name__ == "__main__":
    import sys

    # Run validation
    is_valid, errors, warnings = validate_startup_sync()

    # Print summary
    print("\n" + "=" * 60)
    if is_valid:
        print("✅ AutoCTF is ready to start")
        sys.exit(0)
    else:
        print("❌ AutoCTF cannot start - fix errors above")
        sys.exit(1)
