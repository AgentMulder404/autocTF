from e2b import AsyncSandbox
import asyncio
import os

# Global sandbox instance for reuse
_sandbox = None

async def get_sandbox():
    """Get or create a sandbox instance"""
    global _sandbox
    if _sandbox is None:
        _sandbox = await AsyncSandbox.create()
        print("✅ E2B Sandbox created")

        # Install required security tools
        print("📦 Installing security tools (this may take a minute)...")
        try:
            install_cmd = """
            export DEBIAN_FRONTEND=noninteractive && \
            apt-get update -qq && \
            apt-get install -y -qq nmap nikto gobuster sqlmap curl wget > /dev/null 2>&1 && \
            echo "✅ Security tools installed"
            """
            result = await _sandbox.commands.run(install_cmd, timeout=180)
            if result.exit_code == 0:
                print("✅ Security tools ready")
            else:
                print(f"⚠️ Tool installation warning: {result.stderr[:200]}")
        except Exception as e:
            print(f"⚠️ Failed to install tools: {e}")

    return _sandbox

async def exec_command(command: str, timeout=120):
    """Execute command in E2B sandbox with error handling"""
    try:
        sandbox = await get_sandbox()
        print(f"[Exec MCP] Running: {command}")

        result = await sandbox.commands.run(command, timeout=timeout)

        # Check for command not found errors
        if result.exit_code == 127:
            tool = command.split()[0]
            error_msg = f"Tool '{tool}' not found. Please ensure security tools are installed."
            print(f"❌ {error_msg}")
            raise RuntimeError(error_msg)

        output = result.stdout + "\n" + result.stderr

        # Check for actual errors (non-zero exit codes)
        if result.exit_code != 0 and result.exit_code != 127:
            print(f"⚠️ Command exited with code {result.exit_code}")
            # Don't fail on non-critical errors, just log them

        return output

    except Exception as e:
        error_msg = f"Command execution failed: {str(e)}"
        print(f"❌ {error_msg}")
        raise RuntimeError(error_msg) from e

async def close_sandbox():
    """Close the global sandbox instance"""
    global _sandbox
    if _sandbox:
        try:
            await _sandbox.close()
            print("🔒 Sandbox closed")
        except:
            pass
        _sandbox = None