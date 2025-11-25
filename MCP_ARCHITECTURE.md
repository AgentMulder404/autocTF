# AutoCTF "MCP" Architecture

## Overview

**IMPORTANT**: Despite the directory name `mcp/`, AutoCTF does **NOT** use the Model Context Protocol (MCP). The "MCP" directory contains simple Python wrapper modules that directly call external APIs.

## What is NOT Being Used

- ❌ No MCP servers
- ❌ No MCP client protocol
- ❌ No MCP configuration files (no mcp.json, mcp.yaml)
- ❌ No MCP registration/discovery

## What IS Being Used

AutoCTF uses **three Python helper modules** that wrap external services:

### 1. E2B Exec Client (`mcp/exec_client.py`)
**Purpose**: Execute security tools in an isolated cloud sandbox

**How it works**:
- Creates an E2B AsyncSandbox instance
- Installs security tools (nmap, sqlmap, nikto, gobuster)
- Executes commands and returns output
- Handles tool installation and retries

**API Used**: [E2B Sandbox API](https://e2b.dev)
- **Required Env Var**: `E2B_API_KEY`

**Functions**:
- `get_sandbox()` - Get or create sandbox instance
- `exec_command(command)` - Execute command in sandbox
- `close_sandbox()` - Clean up sandbox

### 2. Browserbase Client (`mcp/browserbase_client.py`)
**Purpose**: Capture screenshots of exploitation proofs

**How it works**:
- Creates browser sessions via Browserbase API
- Navigates to URLs and captures screenshots
- Used for visual proof-of-concept evidence

**API Used**: [Browserbase API](https://browserbase.com)
- **Required Env Vars**:
  - `BROWSERBASE_API_KEY`
  - `BROWSERBASE_PROJECT_ID`

**Functions**:
- `create_session()` - Create browser session
- `screenshot(session_id, url)` - Capture screenshot

### 3. GitHub Client (`mcp/github_client.py`)
**Purpose**: Create pull requests with automated security patches

**How it works**:
- Uses PyGithub library to interact with GitHub API
- Creates branches, commits files, opens PRs
- Generates detailed PR descriptions with exploitation evidence

**API Used**: [GitHub REST API](https://docs.github.com/en/rest)
- **Required Env Vars**:
  - `GITHUB_TOKEN` - Personal access token with repo permissions
  - `GITHUB_REPO` - Format: `owner/repo`

**Functions**:
- `get_repo()` - Get GitHub repository object
- `create_pr(title, body, branch, files, ...)` - Create pull request

## Environment Variable Loading

All modules now load environment variables using `python-dotenv`:

```python
from dotenv import load_dotenv
load_dotenv()
```

This ensures environment variables are available even when modules are imported in background tasks or separate processes.

## Integration Flow

```
Dashboard UI
    ↓
FastAPI Backend (dashboard/backend/main.py)
    ↓
Background Task (pentest_worker.py)
    ↓
Agent Pipeline (agent/main.py)
    ↓
┌─────────────────┬─────────────────┬─────────────────┐
│   Recon Phase   │  Analyze Phase  │  Exploit Phase  │
│  (recon.py)     │  (analyze.py)   │  (exploit.py)   │
└─────────────────┴─────────────────┴─────────────────┘
    ↓                   ↓                   ↓
┌─────────────────┬─────────────────┬─────────────────┐
│ exec_client.py  │    xAI Grok     │ exec_client.py  │
│ (E2B Sandbox)   │   (LLM API)     │ (sqlmap, etc)   │
└─────────────────┴─────────────────┴─────────────────┘
    ↓                                      ↓
browserbase_client.py              github_client.py
(Screenshots)                      (Create PR)
```

## Why "MCP" Naming?

The directory is named `mcp/` but doesn't use MCP protocol because:
1. It was intended to be "Model Communication Protocol" (not Model Context Protocol)
2. Historical naming from early development
3. Simplified architecture - direct API calls are more straightforward than MCP protocol

## Verification

Run the diagnostic script to verify configuration:

```bash
python verify_mcp_config.py
```

This will check:
- ✅ All required environment variables
- ✅ Module imports
- ✅ E2B sandbox connectivity
- ✅ Tool installation in sandbox

## Required Environment Variables

Create a `.env` file in the project root:

```bash
# E2B Sandbox (Required)
E2B_API_KEY=e2b_xxxxx

# Browserbase (Required)
BROWSERBASE_API_KEY=bb_live_xxxxx
BROWSERBASE_PROJECT_ID=xxxxx

# GitHub (Required)
GITHUB_TOKEN=ghp_xxxxx
GITHUB_REPO=username/repo

# LLM Analysis (Required)
XAI_API_KEY=xai-xxxxx

# Dashboard Database (Required)
DATABASE_URL=postgresql://user:pass@host/db

# Optional
OPENAI_API_KEY=sk-xxxxx
```

## Troubleshooting

### "No pentesting actions after entering GitHub repo"

**Possible causes**:
1. ❌ Environment variables not loaded in background task
2. ❌ E2B API key invalid or expired
3. ❌ XAI_API_KEY missing (required for vulnerability analysis)
4. ❌ Dashboard backend not running properly

**Solution**:
```bash
# 1. Verify all env vars are set
python verify_mcp_config.py

# 2. Check dashboard logs
cd dashboard/backend && python main.py
# Look for errors in terminal

# 3. Test E2B connection
python -c "from mcp.exec_client import exec_command; import asyncio; print(asyncio.run(exec_command('echo test')))"
```

### "Module import errors"

**Solution**:
```bash
# Install all dependencies
pip install -r requirements.txt
pip install -r dashboard/backend/requirements.txt

# Verify imports
python -c "from mcp.exec_client import exec_command; print('OK')"
python -c "from agent.analyze import detect_vulns; print('OK')"
```

## Future Improvements

If you want to convert to **actual MCP**:

1. Create MCP server implementations:
   ```
   mcp_servers/
   ├── exec_server.py      # MCP server for E2B
   ├── browser_server.py   # MCP server for Browserbase
   └── github_server.py    # MCP server for GitHub
   ```

2. Implement MCP protocol handlers (JSON-RPC 2.0)

3. Create MCP configuration:
   ```json
   {
     "mcpServers": {
       "exec": {
         "command": "python",
         "args": ["mcp_servers/exec_server.py"]
       }
     }
   }
   ```

4. Use MCP client library to communicate with servers

But for AutoCTF's use case, **direct API calls are simpler and more efficient**.
