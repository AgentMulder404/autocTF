"""
E2B Cloud Sandbox Manager for AutoCTF
Manages remote E2B sandboxes for security testing without Docker
"""

from e2b import AsyncSandbox
import asyncio
import os
from dotenv import load_dotenv
from typing import Optional, Dict, Any
import time

# Load environment variables
load_dotenv()

class SandboxManager:
    """
    Manages E2B cloud sandboxes for pentest execution
    Handles sandbox lifecycle, error recovery, and resource management
    """

    def __init__(self):
        self.sandbox: Optional[AsyncSandbox] = None
        self.api_key = os.getenv('E2B_API_KEY')
        self.created_at = None
        self.command_count = 0
        self.max_sandbox_age = 3600  # 1 hour
        self.max_commands = 100  # Reset after 100 commands

        if not self.api_key:
            raise ValueError("E2B_API_KEY not found in environment variables. Add it to your .env file.")

    async def create_sandbox(self, template: str = "base", timeout: int = 900) -> AsyncSandbox:
        """
        Create a new E2B sandbox instance

        Args:
            template: E2B template to use (default: "base")
            timeout: Sandbox timeout in seconds (default: 900 = 15 min)

        Returns:
            AsyncSandbox instance

        Raises:
            RuntimeError: If sandbox creation fails
        """
        try:
            print(f"🚀 Creating E2B sandbox (timeout: {timeout}s)...")

            # Create sandbox with API key
            self.sandbox = await AsyncSandbox.create(
                timeout=timeout,
                api_key=self.api_key
            )

            self.created_at = time.time()
            self.command_count = 0

            print(f"✅ E2B Sandbox created: {self.sandbox.id[:12]}...")
            return self.sandbox

        except Exception as e:
            error_msg = f"Failed to create E2B sandbox: {str(e)}"
            print(f"❌ {error_msg}")

            # Check for common errors
            if "api_key" in str(e).lower() or "unauthorized" in str(e).lower():
                print("💡 Hint: Check your E2B_API_KEY in .env file")
                print("   Get API key from: https://e2b.dev/dashboard")
            elif "quota" in str(e).lower() or "limit" in str(e).lower():
                print("💡 Hint: You may have hit E2B quota limits")
                print("   Check your usage: https://e2b.dev/dashboard")
            elif "timeout" in str(e).lower():
                print("💡 Hint: Sandbox creation timed out - E2B may be experiencing issues")

            raise RuntimeError(error_msg) from e

    async def get_or_create_sandbox(self) -> AsyncSandbox:
        """
        Get existing sandbox or create new one if needed
        Handles automatic recreation on expiration or quota limits
        """
        # Check if sandbox needs recreation
        should_recreate = False

        if self.sandbox is None:
            should_recreate = True
            print("📦 No sandbox exists, creating new one...")

        elif self.created_at and (time.time() - self.created_at > self.max_sandbox_age):
            should_recreate = True
            print("♻️  Sandbox expired (>1 hour), recreating...")

        elif self.command_count >= self.max_commands:
            should_recreate = True
            print("♻️  Command limit reached, recreating sandbox...")

        if should_recreate:
            await self.close_sandbox()
            await self.create_sandbox()
            await self.install_security_tools()

        return self.sandbox

    async def install_security_tools(self):
        """
        Install required security tools in the sandbox
        Handles apt-get installation with proper error handling
        """
        if not self.sandbox:
            raise RuntimeError("No sandbox available for tool installation")

        print("📦 Installing security tools (this may take 2-3 minutes)...")

        try:
            # Update package lists with timeout and error handling
            print("  → Updating package lists...")
            update_cmd = """
            export DEBIAN_FRONTEND=noninteractive && \
            sudo apt-get update -qq 2>&1 | grep -E "Reading|Fetched|E:|W:" | tail -5
            """

            update_result = await self.sandbox.commands.run(update_cmd, timeout=120)

            if update_result.exit_code != 0:
                print(f"⚠️  Update warning (exit {update_result.exit_code}), continuing anyway...")

            # Install security tools
            tools = [
                "nmap",          # Network scanner
                "nikto",         # Web scanner
                "gobuster",      # Directory brute forcer
                "sqlmap",        # SQL injection tool
                "curl",          # HTTP client
                "wget",          # File downloader
                "git",           # Version control
                "whois",         # Domain lookup
                "dnsutils",      # DNS tools
                "netcat-openbsd" # Network utility
            ]

            install_cmd = f"""
            export DEBIAN_FRONTEND=noninteractive && \
            sudo apt-get install -y -qq {' '.join(tools)} 2>&1 | \
            grep -E "Setting up|Unpacking|Done|E:|W:" | tail -10
            """

            print(f"  → Installing: {', '.join(tools)}")
            result = await self.sandbox.commands.run(install_cmd, timeout=300)

            if result.exit_code != 0:
                print(f"⚠️  Some tools may not have installed (exit {result.exit_code})")
                if result.stderr:
                    print(f"  → Error: {result.stderr[:200]}")

            # Verify installation
            verify_cmd = """
            echo "Checking installed tools:" && \
            for tool in nmap nikto gobuster sqlmap curl wget git; do
                if command -v $tool >/dev/null 2>&1; then
                    echo "  ✓ $tool"
                else
                    echo "  ✗ $tool (missing)"
                fi
            done
            """

            verify_result = await self.sandbox.commands.run(verify_cmd, timeout=30)
            print(verify_result.stdout)

            # Check if critical tools are available
            critical_tools = ["nmap", "sqlmap", "curl"]
            missing_critical = []

            for tool in critical_tools:
                if f"✗ {tool}" in verify_result.stdout or f"✗ {tool}" in str(verify_result.stderr):
                    missing_critical.append(tool)

            if missing_critical:
                print(f"❌ Critical tools missing: {', '.join(missing_critical)}")
                print("⚠️  Pentest scans may fail or produce limited results")
            else:
                print("✅ Security tools installed and verified")

        except asyncio.TimeoutError:
            print("❌ Tool installation timed out (network issues?)")
            print("⚠️  Continuing anyway, but scans will likely fail")
        except Exception as e:
            print(f"❌ Tool installation error: {str(e)}")
            print("⚠️  Continuing anyway, but scans will likely fail")

    async def run_command(self, command: str, timeout: int = 120) -> Dict[str, Any]:
        """
        Run a command in the sandbox with comprehensive error handling

        Args:
            command: Shell command to execute
            timeout: Command timeout in seconds

        Returns:
            Dict with stdout, stderr, exit_code, and success status

        Raises:
            RuntimeError: If sandbox is unavailable or command fails critically
        """
        try:
            # Ensure sandbox exists
            sandbox = await self.get_or_create_sandbox()

            self.command_count += 1
            print(f"[Sandbox] Running command #{self.command_count}: {command[:80]}...")

            # Run command with timeout
            result = await sandbox.commands.run(command, timeout=timeout)

            # Handle command not found errors
            if result.exit_code == 127:
                tool = command.split()[0]
                print(f"❌ Tool '{tool}' not found in sandbox")
                print("🔄 Reinstalling security tools...")

                # Reinstall tools and retry once
                await self.install_security_tools()
                print(f"🔄 Retrying command: {command[:80]}...")
                result = await sandbox.commands.run(command, timeout=timeout)

                if result.exit_code == 127:
                    raise RuntimeError(
                        f"Tool '{tool}' not available even after reinstall. "
                        f"E2B sandbox may not support this tool."
                    )

            # Log warnings for non-zero exits
            if result.exit_code != 0:
                print(f"⚠️  Command exited with code {result.exit_code}")
                if result.stderr and len(result.stderr) < 500:
                    print(f"  → Error: {result.stderr}")

            return {
                'stdout': result.stdout or '',
                'stderr': result.stderr or '',
                'exit_code': result.exit_code,
                'success': result.exit_code == 0,
                'output': (result.stdout or '') + '\n' + (result.stderr or '')
            }

        except asyncio.TimeoutError:
            error_msg = f"Command timed out after {timeout}s: {command[:80]}"
            print(f"⏱️  {error_msg}")
            return {
                'stdout': '',
                'stderr': f"Timeout: Command exceeded {timeout}s limit",
                'exit_code': -1,
                'success': False,
                'output': error_msg
            }

        except Exception as e:
            error_msg = f"Command execution failed: {str(e)}"
            print(f"❌ {error_msg}")

            # Check for quota/rate limit errors
            if "quota" in str(e).lower() or "rate" in str(e).lower():
                print("💡 Hint: You may have hit E2B quota limits")
                print("   Wait a few minutes or upgrade: https://e2b.dev/dashboard")

            return {
                'stdout': '',
                'stderr': error_msg,
                'exit_code': -1,
                'success': False,
                'output': error_msg
            }

    async def close_sandbox(self):
        """
        Close and cleanup sandbox
        E2B sandboxes auto-cleanup on timeout, but manual cleanup is good practice
        """
        if self.sandbox:
            try:
                sandbox_id = self.sandbox.id[:12]
                print(f"🔒 Closing sandbox: {sandbox_id}...")
                # Note: E2B handles cleanup automatically
                self.sandbox = None
                self.created_at = None
                self.command_count = 0
                print("✅ Sandbox closed")
            except Exception as e:
                print(f"⚠️  Sandbox cleanup warning: {e}")
                self.sandbox = None

    async def get_sandbox_info(self) -> Dict[str, Any]:
        """Get information about current sandbox state"""
        if not self.sandbox:
            return {
                'active': False,
                'sandbox_id': None,
                'age_seconds': 0,
                'command_count': 0
            }

        age = int(time.time() - self.created_at) if self.created_at else 0

        return {
            'active': True,
            'sandbox_id': self.sandbox.id,
            'age_seconds': age,
            'command_count': self.command_count,
            'age_minutes': age / 60,
            'will_reset_in': max(0, self.max_sandbox_age - age)
        }


# Global singleton instance
_manager: Optional[SandboxManager] = None

async def get_manager() -> SandboxManager:
    """Get or create global sandbox manager instance"""
    global _manager
    if _manager is None:
        _manager = SandboxManager()
    return _manager

async def run_in_sandbox(command: str, timeout: int = 120) -> str:
    """
    Convenience function to run a command in the managed sandbox

    Args:
        command: Shell command to execute
        timeout: Command timeout in seconds

    Returns:
        Command output (stdout + stderr)
    """
    manager = await get_manager()
    result = await manager.run_command(command, timeout)
    return result['output']

async def cleanup():
    """Cleanup global sandbox manager"""
    global _manager
    if _manager:
        await _manager.close_sandbox()
        _manager = None


if __name__ == "__main__":
    # Test sandbox manager
    async def test():
        print("Testing Sandbox Manager...")
        manager = SandboxManager()

        # Create sandbox
        await manager.create_sandbox()

        # Install tools
        await manager.install_security_tools()

        # Run test command
        result = await manager.run_command("echo 'Hello from E2B!' && nmap --version | head -3")
        print(f"\nTest Result:\n{result['output']}")

        # Get info
        info = await manager.get_sandbox_info()
        print(f"\nSandbox Info: {info}")

        # Cleanup
        await manager.close_sandbox()
        print("\n✅ Test complete!")

    asyncio.run(test())
