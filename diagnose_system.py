#!/usr/bin/env python3
"""
AutoCTF Full System Diagnostic
Tests all subsystems with actual API calls and generates detailed report
"""

import os
import sys
import asyncio
import time
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'

class DiagnosticReport:
    """Store and format diagnostic results"""

    def __init__(self):
        self.results = []
        self.start_time = time.time()

    def add_result(self, subsystem, component, status, message, details=None):
        """Add a test result"""
        self.results.append({
            'subsystem': subsystem,
            'component': component,
            'status': status,  # 'PASS', 'FAIL', 'WARN'
            'message': message,
            'details': details,
            'timestamp': time.time()
        })

    def print_result(self, subsystem, component, status, message):
        """Print a result line"""
        if status == 'PASS':
            icon = f"{Colors.GREEN}✅{Colors.END}"
        elif status == 'FAIL':
            icon = f"{Colors.RED}❌{Colors.END}"
        else:  # WARN
            icon = f"{Colors.YELLOW}⚠️{Colors.END}"

        print(f"  {icon} {component}: {message}")

    def generate_report(self):
        """Generate final report"""
        duration = time.time() - self.start_time

        # Count results
        total = len(self.results)
        passed = len([r for r in self.results if r['status'] == 'PASS'])
        failed = len([r for r in self.results if r['status'] == 'FAIL'])
        warned = len([r for r in self.results if r['status'] == 'WARN'])

        # Group by subsystem
        subsystems = {}
        for result in self.results:
            subsystem = result['subsystem']
            if subsystem not in subsystems:
                subsystems[subsystem] = {'pass': 0, 'fail': 0, 'warn': 0}
            subsystems[subsystem][result['status'].lower()] += 1

        print("\n" + "=" * 70)
        print(f"{Colors.BOLD}📊 DIAGNOSTIC REPORT{Colors.END}")
        print("=" * 70)

        print(f"\n{Colors.CYAN}⏱️  Test Duration:{Colors.END} {duration:.2f}s")
        print(f"{Colors.CYAN}📋 Total Tests:{Colors.END} {total}")
        print(f"{Colors.GREEN}✅ Passed:{Colors.END} {passed}")
        print(f"{Colors.RED}❌ Failed:{Colors.END} {failed}")
        print(f"{Colors.YELLOW}⚠️  Warnings:{Colors.END} {warned}")

        # Subsystem breakdown
        print(f"\n{Colors.BOLD}🔍 Subsystem Breakdown:{Colors.END}")
        print("-" * 70)
        for subsystem, counts in subsystems.items():
            status_icon = "✅" if counts['fail'] == 0 else "❌"
            print(f"  {status_icon} {subsystem}: "
                  f"{Colors.GREEN}{counts['pass']} pass{Colors.END}, "
                  f"{Colors.RED}{counts['fail']} fail{Colors.END}, "
                  f"{Colors.YELLOW}{counts['warn']} warn{Colors.END}")

        # Failed tests details
        if failed > 0:
            print(f"\n{Colors.RED}{Colors.BOLD}❌ FAILED TESTS:{Colors.END}")
            print("-" * 70)
            for result in self.results:
                if result['status'] == 'FAIL':
                    print(f"  • {result['subsystem']} / {result['component']}")
                    print(f"    {result['message']}")
                    if result['details']:
                        print(f"    Details: {result['details']}")

        # Overall status
        print("\n" + "=" * 70)
        if failed == 0:
            print(f"{Colors.GREEN}{Colors.BOLD}✅ SYSTEM STATUS: OPERATIONAL{Colors.END}")
            print(f"\n{Colors.GREEN}All subsystems are functioning correctly.{Colors.END}")
            print(f"{Colors.GREEN}AutoCTF is ready to run pentests!{Colors.END}")
            return 0
        else:
            print(f"{Colors.RED}{Colors.BOLD}❌ SYSTEM STATUS: DEGRADED{Colors.END}")
            print(f"\n{Colors.RED}{failed} critical subsystem(s) failed.{Colors.END}")
            print(f"{Colors.YELLOW}Fix the issues above before running pentests.{Colors.END}")
            return 1

# Initialize report
report = DiagnosticReport()

def test_env_vars():
    """Test 1: Environment Variables"""
    subsystem = "Environment Variables"
    print(f"\n{Colors.BOLD}{Colors.BLUE}[1] {subsystem}{Colors.END}")
    print("-" * 70)

    required_vars = {
        'E2B_API_KEY': 'E2B Sandbox',
        'BROWSERBASE_API_KEY': 'Browserbase Screenshots',
        'BROWSERBASE_PROJECT_ID': 'Browserbase Project',
        'GITHUB_TOKEN': 'GitHub API',
        'GITHUB_REPO': 'GitHub Repository',
        'XAI_API_KEY': 'xAI Grok LLM',
        'DATABASE_URL': 'PostgreSQL Database'
    }

    for var, description in required_vars.items():
        value = os.getenv(var)
        if value:
            masked = f"{value[:10]}..." if len(value) > 10 else value
            report.add_result(subsystem, var, 'PASS', f"Loaded ({masked})")
            report.print_result(subsystem, var, 'PASS', f"Loaded")
        else:
            report.add_result(subsystem, var, 'FAIL', 'Not set',
                            f"Set {var} in .env file")
            report.print_result(subsystem, var, 'FAIL', 'Not set')

def test_mcp_imports():
    """Test 2: MCP Client Imports"""
    subsystem = "MCP Client Modules"
    print(f"\n{Colors.BOLD}{Colors.BLUE}[2] {subsystem}{Colors.END}")
    print("-" * 70)

    modules = {
        'mcp.exec_client': 'E2B Exec Client',
        'mcp.browserbase_client': 'Browserbase Client',
        'mcp.github_client': 'GitHub Client'
    }

    for module, description in modules.items():
        try:
            __import__(module)
            report.add_result(subsystem, description, 'PASS', 'Import successful')
            report.print_result(subsystem, description, 'PASS', 'Import successful')
        except Exception as e:
            report.add_result(subsystem, description, 'FAIL', 'Import failed', str(e))
            report.print_result(subsystem, description, 'FAIL', f'Import failed: {e}')

def test_agent_nodes():
    """Test 3: Agent Pipeline Nodes"""
    subsystem = "Agent Pipeline Nodes"
    print(f"\n{Colors.BOLD}{Colors.BLUE}[3] {subsystem}{Colors.END}")
    print("-" * 70)

    nodes = {
        'agent.recon': 'Reconnaissance Node',
        'agent.analyze': 'Vulnerability Analysis Node',
        'agent.exploit': 'Exploitation Node',
    }

    for module, description in nodes.items():
        try:
            mod = __import__(module, fromlist=[''])

            # Check for expected functions
            if module == 'agent.recon' and hasattr(mod, 'run_recon'):
                report.add_result(subsystem, description, 'PASS', 'Node reachable, run_recon() found')
                report.print_result(subsystem, description, 'PASS', 'Reachable')
            elif module == 'agent.analyze' and hasattr(mod, 'detect_vulns'):
                report.add_result(subsystem, description, 'PASS', 'Node reachable, detect_vulns() found')
                report.print_result(subsystem, description, 'PASS', 'Reachable')
            elif module == 'agent.exploit' and hasattr(mod, 'try_sqli'):
                report.add_result(subsystem, description, 'PASS', 'Node reachable, try_sqli() found')
                report.print_result(subsystem, description, 'PASS', 'Reachable')
            else:
                report.add_result(subsystem, description, 'WARN', 'Imported but missing expected functions')
                report.print_result(subsystem, description, 'WARN', 'Missing functions')
        except Exception as e:
            report.add_result(subsystem, description, 'FAIL', 'Node unreachable', str(e))
            report.print_result(subsystem, description, 'FAIL', f'Unreachable: {e}')

async def test_e2b_connection():
    """Test 4: E2B Sandbox Connection"""
    subsystem = "E2B Sandbox"
    print(f"\n{Colors.BOLD}{Colors.BLUE}[4] {subsystem}{Colors.END}")
    print("-" * 70)

    try:
        from e2b import AsyncSandbox

        print(f"  {Colors.CYAN}→ Creating sandbox...{Colors.END}")
        sandbox = await AsyncSandbox.create(timeout=30)
        report.add_result(subsystem, 'Sandbox Creation', 'PASS', 'Sandbox created successfully')
        report.print_result(subsystem, 'Sandbox Creation', 'PASS', 'Created successfully')

        # Test command execution
        print(f"  {Colors.CYAN}→ Testing command execution...{Colors.END}")
        result = await sandbox.commands.run("echo 'AutoCTF Test'")
        if "AutoCTF Test" in result.stdout:
            report.add_result(subsystem, 'Command Execution', 'PASS', 'Commands execute correctly')
            report.print_result(subsystem, 'Command Execution', 'PASS', 'Verified')
        else:
            report.add_result(subsystem, 'Command Execution', 'FAIL', 'Command output incorrect')
            report.print_result(subsystem, 'Command Execution', 'FAIL', 'Output incorrect')

        # Test tool availability (quick check)
        print(f"  {Colors.CYAN}→ Checking security tools...{Colors.END}")
        tool_check = await sandbox.commands.run("command -v nmap curl || echo 'tools_missing'")
        if "nmap" in tool_check.stdout and tool_check.exit_code == 0:
            report.add_result(subsystem, 'Security Tools', 'PASS', 'Tools pre-installed')
            report.print_result(subsystem, 'Security Tools', 'PASS', 'Pre-installed')
        elif "tools_missing" in tool_check.stdout or tool_check.exit_code != 0:
            report.add_result(subsystem, 'Security Tools', 'WARN', 'Tools will be installed on first run (expected)')
            report.print_result(subsystem, 'Security Tools', 'WARN', 'Will auto-install')
        else:
            report.add_result(subsystem, 'Security Tools', 'PASS', 'Tools available')
            report.print_result(subsystem, 'Security Tools', 'PASS', 'Available')

    except Exception as e:
        report.add_result(subsystem, 'E2B Connection', 'FAIL', 'Connection failed', str(e))
        report.print_result(subsystem, 'E2B Connection', 'FAIL', f'Failed: {e}')

async def test_github_auth():
    """Test 5: GitHub API Authentication"""
    subsystem = "GitHub API"
    print(f"\n{Colors.BOLD}{Colors.BLUE}[5] {subsystem}{Colors.END}")
    print("-" * 70)

    try:
        from github import Github
        import github

        token = os.getenv('GITHUB_TOKEN')
        repo_name = os.getenv('GITHUB_REPO')

        if not token or not repo_name:
            report.add_result(subsystem, 'Configuration', 'FAIL', 'GITHUB_TOKEN or GITHUB_REPO not set')
            report.print_result(subsystem, 'Configuration', 'FAIL', 'Missing env vars')
            return

        # Check if token looks like a placeholder
        if token.count('x') > 20 or token == 'ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxx':
            report.add_result(subsystem, 'Configuration', 'FAIL',
                            'GITHUB_TOKEN appears to be a placeholder',
                            'Replace with real token from https://github.com/settings/tokens')
            report.print_result(subsystem, 'Configuration', 'FAIL', 'Token is placeholder')
            return

        print(f"  {Colors.CYAN}→ Authenticating...{Colors.END}")
        # Use new Auth API to avoid deprecation warning
        auth = github.Auth.Token(token)
        g = Github(auth=auth)

        # Test authentication
        user = g.get_user()
        username = user.login
        report.add_result(subsystem, 'Authentication', 'PASS', f'Authenticated as {username}')
        report.print_result(subsystem, 'Authentication', 'PASS', f'Logged in as {username}')

        # Test repository access
        print(f"  {Colors.CYAN}→ Testing repo access...{Colors.END}")
        repo = g.get_repo(repo_name)
        report.add_result(subsystem, 'Repository Access', 'PASS', f'Can access {repo.name}')
        report.print_result(subsystem, 'Repository Access', 'PASS', f'Repo: {repo.name}')

        # Check permissions
        permissions = repo.permissions
        can_push = permissions.push
        can_pr = permissions.pull

        if can_push:
            report.add_result(subsystem, 'Write Permissions', 'PASS', 'Can create branches and PRs')
            report.print_result(subsystem, 'Write Permissions', 'PASS', 'Can create PRs')
        else:
            report.add_result(subsystem, 'Write Permissions', 'WARN',
                            'Limited permissions, PR creation may fail')
            report.print_result(subsystem, 'Write Permissions', 'WARN', 'Limited permissions')

    except Exception as e:
        report.add_result(subsystem, 'GitHub API', 'FAIL', 'API test failed', str(e))
        report.print_result(subsystem, 'GitHub API', 'FAIL', f'Failed: {e}')

async def test_browserbase():
    """Test 6: Browserbase Session"""
    subsystem = "Browserbase"
    print(f"\n{Colors.BOLD}{Colors.BLUE}[6] {subsystem}{Colors.END}")
    print("-" * 70)

    try:
        from browserbase import Browserbase

        api_key = os.getenv('BROWSERBASE_API_KEY')
        project_id = os.getenv('BROWSERBASE_PROJECT_ID')

        if not api_key or not project_id:
            report.add_result(subsystem, 'Configuration', 'FAIL', 'API key or project ID not set')
            report.print_result(subsystem, 'Configuration', 'FAIL', 'Missing env vars')
            return

        print(f"  {Colors.CYAN}→ Creating session...{Colors.END}")
        bb = Browserbase(api_key=api_key)
        session = bb.sessions.create(project_id=project_id)

        if session and hasattr(session, 'id'):
            report.add_result(subsystem, 'Session Creation', 'PASS', f'Session created: {session.id[:20]}...')
            report.print_result(subsystem, 'Session Creation', 'PASS', 'Session created')
        else:
            report.add_result(subsystem, 'Session Creation', 'WARN', 'Session created but ID not available')
            report.print_result(subsystem, 'Session Creation', 'WARN', 'Partial success')

    except Exception as e:
        error_msg = str(e)
        if "401" in error_msg or "unauthorized" in error_msg.lower():
            report.add_result(subsystem, 'Browserbase API', 'FAIL', 'Authentication failed', error_msg)
            report.print_result(subsystem, 'Browserbase API', 'FAIL', 'Auth failed')
        elif "404" in error_msg or "not found" in error_msg.lower():
            report.add_result(subsystem, 'Browserbase API', 'FAIL', 'Project ID invalid', error_msg)
            report.print_result(subsystem, 'Browserbase API', 'FAIL', 'Invalid project ID')
        else:
            report.add_result(subsystem, 'Browserbase API', 'FAIL', 'API test failed', error_msg)
            report.print_result(subsystem, 'Browserbase API', 'FAIL', f'Failed: {error_msg[:50]}')

async def test_xai_api():
    """Test 7: xAI Grok API"""
    subsystem = "xAI Grok LLM"
    print(f"\n{Colors.BOLD}{Colors.BLUE}[7] {subsystem}{Colors.END}")
    print("-" * 70)

    try:
        import requests

        api_key = os.getenv('XAI_API_KEY')

        if not api_key:
            report.add_result(subsystem, 'Configuration', 'FAIL', 'XAI_API_KEY not set')
            report.print_result(subsystem, 'Configuration', 'FAIL', 'Missing API key')
            return

        print(f"  {Colors.CYAN}→ Testing API connection...{Colors.END}")

        payload = {
            "model": "grok-2-1212",
            "messages": [{"role": "user", "content": "Test"}],
            "max_tokens": 10
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

        response = requests.post(
            "https://api.x.ai/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )

        if response.status_code == 200:
            report.add_result(subsystem, 'API Connection', 'PASS', 'API responding correctly')
            report.print_result(subsystem, 'API Connection', 'PASS', 'API responding')

            # Check response format
            data = response.json()
            if 'choices' in data and len(data['choices']) > 0:
                report.add_result(subsystem, 'Response Format', 'PASS', 'Valid response format')
                report.print_result(subsystem, 'Response Format', 'PASS', 'Valid format')
            else:
                report.add_result(subsystem, 'Response Format', 'WARN', 'Unexpected response format')
                report.print_result(subsystem, 'Response Format', 'WARN', 'Unexpected format')
        else:
            report.add_result(subsystem, 'API Connection', 'FAIL',
                            f'API returned {response.status_code}', response.text[:200])
            report.print_result(subsystem, 'API Connection', 'FAIL',
                              f'Status {response.status_code}')

    except Exception as e:
        report.add_result(subsystem, 'xAI API', 'FAIL', 'API test failed', str(e))
        report.print_result(subsystem, 'xAI API', 'FAIL', f'Failed: {e}')

def test_repo_paths():
    """Test 8: Repository Cloning Paths"""
    subsystem = "Repository Paths"
    print(f"\n{Colors.BOLD}{Colors.BLUE}[8] {subsystem}{Colors.END}")
    print("-" * 70)

    paths = {
        '/tmp': 'Temp directory for cloning',
        '/tmp/sqlmap_dumps': 'SQLMap output directory (auto-created)',
    }

    for path, description in paths.items():
        if os.path.exists(path):
            # Check if writable
            if os.access(path, os.W_OK):
                report.add_result(subsystem, description, 'PASS', f'Path exists and writable: {path}')
                report.print_result(subsystem, description, 'PASS', f'Writable')
            else:
                report.add_result(subsystem, description, 'WARN', f'Path exists but not writable: {path}')
                report.print_result(subsystem, description, 'WARN', 'Not writable')
        else:
            # Try to create it
            try:
                os.makedirs(path, exist_ok=True)
                report.add_result(subsystem, description, 'PASS', f'Path created: {path}')
                report.print_result(subsystem, description, 'PASS', 'Created')
            except Exception as e:
                report.add_result(subsystem, description, 'FAIL', f'Cannot create path: {path}', str(e))
                report.print_result(subsystem, description, 'FAIL', f'Cannot create')

def test_dashboard_imports():
    """Test 9: Dashboard Backend"""
    subsystem = "Dashboard Backend"
    print(f"\n{Colors.BOLD}{Colors.BLUE}[9] {subsystem}{Colors.END}")
    print("-" * 70)

    # Add dashboard paths to Python path
    dashboard_path = os.path.join(os.path.dirname(__file__), 'dashboard', 'backend')
    if os.path.exists(dashboard_path):
        sys.path.insert(0, dashboard_path)

    modules = {
        'models': 'Database Models',
        'schemas': 'Pydantic Schemas',
        'pentest_worker': 'Pentest Worker',
    }

    for module, description in modules.items():
        try:
            __import__(module)
            report.add_result(subsystem, description, 'PASS', 'Module importable')
            report.print_result(subsystem, description, 'PASS', 'Importable')
        except Exception as e:
            report.add_result(subsystem, description, 'FAIL', 'Import failed', str(e))
            report.print_result(subsystem, description, 'FAIL', f'Import failed')

async def main():
    """Run all diagnostics"""
    print(f"""
{Colors.BOLD}{Colors.CYAN}╔════════════════════════════════════════════════════════════════════╗
║                                                                    ║
║              AutoCTF Full System Diagnostic v2.0                   ║
║                                                                    ║
║         Comprehensive testing of all subsystems and APIs           ║
║                                                                    ║
╚════════════════════════════════════════════════════════════════════╝{Colors.END}
""")

    print(f"{Colors.BOLD}Starting diagnostic scan...{Colors.END}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Run all tests
    test_env_vars()
    test_mcp_imports()
    test_agent_nodes()
    await test_e2b_connection()
    await test_github_auth()
    await test_browserbase()
    await test_xai_api()
    test_repo_paths()
    test_dashboard_imports()

    # Generate final report
    exit_code = report.generate_report()

    # Recommendations
    if exit_code == 0:
        print(f"\n{Colors.GREEN}{Colors.BOLD}🚀 RECOMMENDED NEXT STEPS:{Colors.END}")
        print(f"{Colors.GREEN}  1. Start dashboard: ./start-dashboard.sh{Colors.END}")
        print(f"{Colors.GREEN}  2. Open browser: http://localhost:3000{Colors.END}")
        print(f"{Colors.GREEN}  3. Add a target (GitHub repo or web URL){Colors.END}")
        print(f"{Colors.GREEN}  4. Click 'Start Scan' to run pentest{Colors.END}")
    else:
        print(f"\n{Colors.YELLOW}{Colors.BOLD}🔧 RECOMMENDED FIXES:{Colors.END}")
        print(f"{Colors.YELLOW}  1. Check .env file has all required variables{Colors.END}")
        print(f"{Colors.YELLOW}  2. Verify API keys are valid and not expired{Colors.END}")
        print(f"{Colors.YELLOW}  3. Run: pip install -r requirements.txt{Colors.END}")
        print(f"{Colors.YELLOW}  4. Re-run this diagnostic: python3 diagnose_system.py{Colors.END}")

    print("\n" + "=" * 70 + "\n")
    sys.exit(exit_code)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Diagnostic interrupted by user{Colors.END}")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n{Colors.RED}Fatal error: {e}{Colors.END}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
