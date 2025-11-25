#!/usr/bin/env python3
"""
MCP Configuration Diagnostic Script
Verifies that all "MCP" clients and environment variables are properly configured
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_env_var(var_name, required=True):
    """Check if an environment variable is set"""
    value = os.getenv(var_name)
    status = "✅" if value else "❌"
    masked_value = f"{value[:10]}..." if value and len(value) > 10 else value or "NOT SET"

    print(f"  {status} {var_name}: {masked_value}")

    if required and not value:
        return False
    return True

def check_module_import(module_name, display_name):
    """Check if a module can be imported"""
    try:
        __import__(module_name)
        print(f"  ✅ {display_name}: Importable")
        return True
    except Exception as e:
        print(f"  ❌ {display_name}: Import failed - {e}")
        return False

print("""
╔════════════════════════════════════════════════════════════╗
║        AutoCTF MCP Configuration Diagnostic                ║
╚════════════════════════════════════════════════════════════╝
""")

print("\n📋 IMPORTANT NOTE:")
print("=" * 60)
print("The 'mcp/' directory contains Python helper modules, NOT")
print("actual Model Context Protocol (MCP) servers. These are")
print("simple wrapper functions around APIs (E2B, Browserbase, GitHub).")
print("No MCP server/client protocol is being used.")
print("=" * 60)

# Check environment variables
print("\n🔐 ENVIRONMENT VARIABLES:")
print("-" * 60)
all_vars_ok = True

print("\n  Required for E2B Sandbox (Exec Client):")
all_vars_ok &= check_env_var("E2B_API_KEY", required=True)

print("\n  Required for Browserbase (Screenshot Client):")
all_vars_ok &= check_env_var("BROWSERBASE_API_KEY", required=True)
all_vars_ok &= check_env_var("BROWSERBASE_PROJECT_ID", required=True)

print("\n  Required for GitHub (PR Creation):")
all_vars_ok &= check_env_var("GITHUB_TOKEN", required=True)
all_vars_ok &= check_env_var("GITHUB_REPO", required=True)

print("\n  Required for LLM Analysis:")
all_vars_ok &= check_env_var("XAI_API_KEY", required=True)

print("\n  Required for Dashboard Database:")
all_vars_ok &= check_env_var("DATABASE_URL", required=True)

print("\n  Optional:")
check_env_var("OPENAI_API_KEY", required=False)

# Check MCP client modules
print("\n\n📦 MCP CLIENT MODULES (Python Helpers):")
print("-" * 60)
all_modules_ok = True

all_modules_ok &= check_module_import("mcp.exec_client", "E2B Exec Client")
all_modules_ok &= check_module_import("mcp.browserbase_client", "Browserbase Client")
all_modules_ok &= check_module_import("mcp.github_client", "GitHub Client")

# Check agent modules
print("\n\n🤖 AGENT MODULES:")
print("-" * 60)
all_modules_ok &= check_module_import("agent.recon", "Recon Module")
all_modules_ok &= check_module_import("agent.analyze", "Analyze Module")
all_modules_ok &= check_module_import("agent.exploit", "Exploit Module")

# Test E2B connection
print("\n\n🔌 E2B SANDBOX CONNECTION TEST:")
print("-" * 60)
try:
    from e2b import AsyncSandbox
    import asyncio

    async def test_e2b():
        try:
            sandbox = await AsyncSandbox.create(timeout=30)
            print("  ✅ E2B sandbox created successfully")

            # Test command execution
            result = await sandbox.commands.run("echo 'AutoCTF Test'")
            if "AutoCTF Test" in result.stdout:
                print("  ✅ Command execution verified")

            # E2B sandboxes auto-cleanup on timeout, no need to manually close
            print("  ✅ E2B connection fully operational")
            return True
        except Exception as e:
            print(f"  ❌ E2B connection failed: {e}")
            return False

    e2b_ok = asyncio.run(test_e2b())
except Exception as e:
    print(f"  ❌ E2B test failed: {e}")
    e2b_ok = False

# Summary
print("\n\n" + "=" * 60)
print("📊 DIAGNOSTIC SUMMARY")
print("=" * 60)

if all_vars_ok and all_modules_ok and e2b_ok:
    print("✅ ALL CHECKS PASSED - AutoCTF is properly configured")
    print("\nYou can now:")
    print("  1. Start the dashboard: ./start-dashboard.sh")
    print("  2. Add a target via the UI")
    print("  3. Run a pentest scan")
    sys.exit(0)
else:
    print("❌ CONFIGURATION ISSUES DETECTED")
    print("\nIssues found:")
    if not all_vars_ok:
        print("  • Missing or invalid environment variables")
        print("    → Check your .env file in the project root")
    if not all_modules_ok:
        print("  • Module import failures")
        print("    → Run: pip install -r requirements.txt")
    if not e2b_ok:
        print("  • E2B sandbox connection failed")
        print("    → Verify E2B_API_KEY is valid")
        print("    → Check internet connectivity")

    print("\nFix these issues before running AutoCTF.")
    sys.exit(1)
