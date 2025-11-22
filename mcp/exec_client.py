from e2b import AsyncSandbox
import asyncio
import os

# Global sandbox instance for reuse
_sandbox = None

async def get_sandbox():
    """Get or create a sandbox instance"""
    global _sandbox
    if _sandbox is None:
        # Create sandbox with longer timeout (15 minutes)
        _sandbox = await AsyncSandbox.create(timeout=900)
        print("✅ E2B Sandbox created (15 min timeout)")

        # Install required security tools
        print("📦 Installing security tools (this may take up to 3 minutes)...")
        try:
            # First, update package lists (with sudo)
            update_cmd = "sudo apt-get update -qq"
            print("  → Updating package lists...")
            update_result = await _sandbox.commands.run(update_cmd, timeout=120)
            print(f"  → Update exit code: {update_result.exit_code}")

            # Install tools one by one for better visibility (with sudo)
            tools = ["nmap", "nikto", "gobuster", "sqlmap", "curl", "wget", "git", "whois", "dnsutils"]
            install_cmd = f"""
            export DEBIAN_FRONTEND=noninteractive && \
            sudo apt-get install -y -qq {' '.join(tools)} 2>&1 | grep -E "Setting up|Unpacking|E:|W:" || true
            """

            print(f"  → Installing tools: {', '.join(tools)}")
            result = await _sandbox.commands.run(install_cmd, timeout=300)

            if result.stdout:
                print(f"  → Install output: {result.stdout[:500]}")
            if result.stderr:
                print(f"  → Install stderr: {result.stderr[:500]}")

            # Verify tools are installed
            verify_cmd = "command -v nmap && command -v nikto && command -v gobuster && command -v sqlmap && echo 'ALL_TOOLS_OK'"
            verify_result = await _sandbox.commands.run(verify_cmd, timeout=30)

            if "ALL_TOOLS_OK" in verify_result.stdout:
                print("✅ Security tools verified and ready")
            else:
                error_msg = f"Tool verification failed. Some tools may not be installed correctly."
                print(f"❌ {error_msg}")
                print(f"  → Verify output: {verify_result.stdout}")
                print(f"  → Verify stderr: {verify_result.stderr}")
                # Don't fail completely, but log the issue
                print("⚠️ Continuing anyway, but some scans may fail...")

        except Exception as e:
            error_msg = f"Failed to install security tools: {str(e)}"
            print(f"❌ {error_msg}")
            print("⚠️ Sandbox created but tools unavailable. Scans will likely fail.")
            # Don't fail completely to avoid breaking the whole system

    return _sandbox

async def exec_command(command: str, timeout=120):
    """Execute command in E2B sandbox with error handling"""
    try:
        sandbox = await get_sandbox()
        print(f"[Exec MCP] Running: {command[:100]}...")

        result = await sandbox.commands.run(command, timeout=timeout)

        # Check for command not found errors
        if result.exit_code == 127:
            tool = command.split()[0]
            error_msg = f"❌ Tool '{tool}' not found in E2B sandbox"
            print(error_msg)
            print(f"   Exit code: {result.exit_code}")
            print(f"   Stdout: {result.stdout[:200]}")
            print(f"   Stderr: {result.stderr[:200]}")

            # Try to reinstall tools
            print("🔄 Attempting to reinstall security tools...")
            global _sandbox
            _sandbox = None  # Force recreation
            sandbox = await get_sandbox()

            # Retry the command once
            print(f"🔄 Retrying command: {command[:100]}...")
            result = await sandbox.commands.run(command, timeout=timeout)

            if result.exit_code == 127:
                raise RuntimeError(f"Tool '{tool}' still not found after reinstall attempt. E2B sandbox may not support required packages.")

        output = result.stdout + "\n" + result.stderr

        # Check for actual errors (non-zero exit codes)
        if result.exit_code != 0 and result.exit_code != 127:
            print(f"⚠️ Command exited with code {result.exit_code}")
            if result.stderr:
                print(f"   Stderr: {result.stderr[:300]}")

        return output

    except Exception as e:
        error_msg = f"Command execution failed: {str(e)}"
        print(f"❌ {error_msg}")
        # Include more context in the error
        if hasattr(e, '__cause__') and e.__cause__:
            print(f"   Root cause: {str(e.__cause__)}")
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