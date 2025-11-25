# AutoCTF System Diagnostics

## Overview

AutoCTF includes two diagnostic tools to verify system configuration:

1. **`verify_mcp_config.py`** - Quick configuration check (basic)
2. **`diagnose_system.py`** - Full system diagnostic with API tests (comprehensive)

## Quick Start

### Basic Configuration Check
```bash
python3 verify_mcp_config.py
```

This performs basic checks:
- ✅ Environment variables loaded
- ✅ MCP modules importable
- ✅ E2B sandbox connectivity

**Use this for**: Quick verification during setup

### Full System Diagnostic
```bash
python3 diagnose_system.py
```

This performs comprehensive testing:
- ✅ All environment variables
- ✅ MCP client module imports
- ✅ Agent pipeline nodes (recon, analyze, exploit)
- ✅ E2B Sandbox creation and command execution
- ✅ GitHub API authentication and repository access
- ✅ Browserbase session creation
- ✅ xAI Grok API connection
- ✅ Repository cloning paths
- ✅ Dashboard backend modules

**Use this for**: Pre-deployment verification, troubleshooting

## Diagnostic Report Format

The full diagnostic generates a detailed report with:

### Test Results
Each test shows:
- ✅ **PASS** - Test succeeded
- ❌ **FAIL** - Critical failure, fix required
- ⚠️ **WARN** - Non-critical issue, may impact functionality

### Subsystem Breakdown
```
📊 DIAGNOSTIC REPORT
⏱️  Test Duration: 9.22s
📋 Total Tests: 25
✅ Passed: 23
❌ Failed: 2
⚠️  Warnings: 0

🔍 Subsystem Breakdown:
  ✅ Environment Variables: 7 pass, 0 fail, 0 warn
  ✅ MCP Client Modules: 3 pass, 0 fail, 0 warn
  ✅ Agent Pipeline Nodes: 3 pass, 0 fail, 0 warn
  ❌ E2B Sandbox: 2 pass, 1 fail, 0 warn
  ❌ GitHub API: 0 pass, 1 fail, 0 warn
  ✅ Browserbase: 1 pass, 0 fail, 0 warn
  ✅ xAI Grok LLM: 2 pass, 0 fail, 0 warn
  ✅ Repository Paths: 2 pass, 0 fail, 0 warn
  ✅ Dashboard Backend: 3 pass, 0 fail, 0 warn
```

### System Status
- **✅ OPERATIONAL** - All tests passed, ready to run
- **❌ DEGRADED** - Critical failures detected, fix required

## Subsystems Tested

### 1. Environment Variables
Tests all required environment variables are set:
- `E2B_API_KEY` - E2B Sandbox for security tools
- `BROWSERBASE_API_KEY` - Screenshot capture
- `BROWSERBASE_PROJECT_ID` - Browserbase project
- `GITHUB_TOKEN` - GitHub API access
- `GITHUB_REPO` - Target repository
- `XAI_API_KEY` - xAI Grok LLM for analysis
- `DATABASE_URL` - PostgreSQL database connection

### 2. MCP Client Modules
Verifies all "MCP" (API wrapper) modules can be imported:
- `mcp.exec_client` - E2B Sandbox client
- `mcp.browserbase_client` - Browserbase client
- `mcp.github_client` - GitHub client

### 3. Agent Pipeline Nodes
Checks agent modules are reachable with required functions:
- `agent.recon.run_recon()` - Reconnaissance
- `agent.analyze.detect_vulns()` - Vulnerability analysis
- `agent.exploit.try_sqli()` - Exploitation

### 4. E2B Sandbox
Tests actual E2B Sandbox connectivity:
- Creates a sandbox instance
- Executes test command
- Checks security tools availability

### 5. GitHub API
Tests GitHub authentication and permissions:
- Authenticates with token
- Accesses target repository
- Verifies write permissions for PR creation

### 6. Browserbase
Tests Browserbase session creation:
- Creates browser session
- Verifies session ID returned

### 7. xAI Grok LLM
Tests xAI API connectivity:
- Sends test request to Grok
- Verifies response format

### 8. Repository Paths
Checks filesystem paths:
- `/tmp` - Temporary directory for cloning
- `/tmp/sqlmap_dumps` - SQLMap output directory

### 9. Dashboard Backend
Verifies dashboard modules:
- `models` - Database models
- `schemas` - Pydantic schemas
- `pentest_worker` - Background pentest worker

## Common Issues and Fixes

### ❌ E2B Sandbox: Tools need installation
**Status**: ⚠️ WARNING (expected)

**Cause**: Security tools (nmap, sqlmap, etc.) aren't pre-installed in E2B sandboxes

**Fix**: No action needed - tools auto-install on first pentest run

### ❌ GitHub API: Bad credentials (401)
**Cause**: Invalid or expired GitHub token

**Fix**:
```bash
# Generate new token at: https://github.com/settings/tokens
# Required scopes: repo, workflow

# Update .env
GITHUB_TOKEN=ghp_your_real_token_here
GITHUB_REPO=username/repo
```

### ❌ GitHub API: Token is placeholder
**Cause**: Using example token from documentation

**Fix**: Replace placeholder token with real token (see above)

### ❌ Browserbase: Authentication failed
**Cause**: Invalid Browserbase API key or project ID

**Fix**:
```bash
# Get credentials from: https://browserbase.com
# Update .env
BROWSERBASE_API_KEY=bb_live_your_key_here
BROWSERBASE_PROJECT_ID=your-project-id
```

### ❌ xAI API: Connection failed
**Cause**: Invalid xAI API key

**Fix**:
```bash
# Get API key from: https://x.ai
# Update .env
XAI_API_KEY=xai-your-key-here
```

### ❌ Module import failed
**Cause**: Missing dependencies

**Fix**:
```bash
# Install all dependencies
pip install -r requirements.txt
pip install -r dashboard/backend/requirements.txt

# Verify
python3 -c "from mcp.exec_client import exec_command; print('OK')"
```

## Exit Codes

- `0` - All tests passed, system operational
- `1` - One or more tests failed, fix required

## Integration with CI/CD

Use the diagnostic in your CI/CD pipeline:

```yaml
# .github/workflows/test.yml
name: AutoCTF Diagnostics

on: [push, pull_request]

jobs:
  diagnose:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run diagnostics
        env:
          E2B_API_KEY: ${{ secrets.E2B_API_KEY }}
          BROWSERBASE_API_KEY: ${{ secrets.BROWSERBASE_API_KEY }}
          BROWSERBASE_PROJECT_ID: ${{ secrets.BROWSERBASE_PROJECT_ID }}
          GITHUB_TOKEN: ${{ secrets.GH_TOKEN }}
          GITHUB_REPO: ${{ github.repository }}
          XAI_API_KEY: ${{ secrets.XAI_API_KEY }}
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
        run: python3 diagnose_system.py
```

## Automated Monitoring

Schedule regular diagnostics:

```bash
# Add to crontab
0 */6 * * * cd /path/to/autocTF && python3 diagnose_system.py > /var/log/autoctf-diagnostic.log 2>&1
```

## Troubleshooting Tips

### All tests pass but pentests still fail
1. Check dashboard logs: `cd dashboard/backend && python main.py`
2. Verify target URL is accessible
3. Check database connectivity
4. Review pentest worker logs

### Diagnostic hangs on E2B test
- E2B sandbox creation can take 10-30 seconds
- If timeout exceeds 60s, check internet connectivity
- Verify E2B API status: https://status.e2b.dev

### Diagnostic shows old cached results
- Environment variables are loaded via `python-dotenv`
- Changes to `.env` require re-running the diagnostic
- Kill any running Python processes if imports are cached

## Getting Help

If diagnostics fail and you can't resolve:

1. **Save diagnostic output**:
   ```bash
   python3 diagnose_system.py > diagnostic-report.txt 2>&1
   ```

2. **Check logs**:
   ```bash
   # Dashboard logs
   cat dashboard/backend/logs/*.log

   # System logs
   journalctl -u autoctf
   ```

3. **Open issue**: https://github.com/AgentMulder404/autocTF/issues
   - Include diagnostic report
   - Include relevant logs
   - Describe expected vs actual behavior

## Related Documentation

- [MCP Architecture](MCP_ARCHITECTURE.md) - Understand the "MCP" (API wrapper) design
- [CLAUDE.md](CLAUDE.md) - Project overview and commands
- [README.md](README.md) - Getting started guide

## Version History

- **v2.0** - Full system diagnostic with API testing
- **v1.0** - Basic configuration verification

---

**Last Updated**: 2025-11-24
**Maintainer**: AutoCTF Team
