# AutoCTF Startup Validation & Fail-Fast Error Handling

## Overview

AutoCTF now includes comprehensive startup validation and fail-fast error handling to prevent silent failures. The dashboard will **explicitly show errors** instead of silently doing nothing when critical services are misconfigured.

## Features

### 1. Startup Validation (`startup_validation.py`)

Validates all critical services **before** allowing pentests to run:

✅ **Environment Variables** - All required variables loaded
✅ **GitHub API** - Token valid, repository accessible, write permissions verified
✅ **Browserbase** - API key valid, not rate-limited, session creation working
✅ **E2B Sandbox** - Sandbox creation and command execution tested
✅ **xAI Grok** - LLM API responding correctly
✅ **MCP Modules** - All modules importable and responding

### 2. Fail-Fast Error Messages

Instead of silent failures, you now get:
- ❌ **Clear error messages** in dashboard API logs
- ❌ **HTTP 503 errors** when trying to start scans with misconfigured services
- ❌ **Detailed error objects** with actionable fixes
- ✅ **Validation status endpoint** at `/api/validation`

### 3. Improved Browserbase Client

New features to handle rate limiting:

✅ **Session Reuse** - Reuses sessions within 5-minute window
✅ **Automatic Retry** - Retries with exponential backoff on failures
✅ **Rate Limit Detection** - Explicitly logs and handles 429 errors
✅ **Automatic Cleanup** - Closes sessions on exit with `atexit` hook
✅ **Graceful Degradation** - Pentests continue without screenshots if Browserbase unavailable

### 4. Enhanced GitHub Client

Robust authentication with validation:

✅ **Token Validation** - Detects placeholder tokens on startup
✅ **Scope Verification** - Confirms `repo` and `workflow` scopes
✅ **Permission Checks** - Verifies write access to repository
✅ **Rate Limit Monitoring** - Warns when API rate limit is low
✅ **Clear Error Messages** - Actionable errors for 401, 403, 404 responses

## Usage

### Run Standalone Validation

```bash
# Quick validation
python3 startup_validation.py

# Validation runs automatically when dashboard starts
./start-dashboard.sh
```

### Check Validation Status

```bash
# Via API
curl http://localhost:8000/api/validation

# Response format:
{
  "validated": true,
  "is_valid": false,
  "errors": [
    "GITHUB_TOKEN appears to be a placeholder",
    "Browserbase rate limit exceeded"
  ],
  "warnings": [],
  "timestamp": "2025-11-24T19:45:00.000Z"
}
```

### Dashboard Behavior

#### ✅ When All Validations Pass:

```
🚀 AutoCTF Dashboard API starting...
============================================================
✅ Database initialized

🔍 Running startup validation...
[1/6] Environment Variables...
  ✅ E2B_API_KEY: OK
  ✅ GITHUB_TOKEN: OK
  ...
[2/6] GitHub API Authentication...
  ✅ Authenticated as: AgentMulder404
  ✅ Repository access: autocTF
  ✅ Write permissions: OK
  ...
============================================================
✅ Startup validation passed - AutoCTF ready!
============================================================

🌐 Dashboard API ready at http://localhost:8000
```

#### ❌ When Validation Fails:

```
🚀 AutoCTF Dashboard API starting...
============================================================
✅ Database initialized

🔍 Running startup validation...
[1/6] Environment Variables...
  ✅ E2B_API_KEY: OK
  ❌ GITHUB_TOKEN: PLACEHOLDER
  ...
[5/6] GitHub API...
  ❌ Configuration: Token is placeholder

============================================================
❌ CRITICAL: Startup validation failed!
============================================================

🚨 Errors:
  • GITHUB_TOKEN appears to be a placeholder - replace with real token
  • Browserbase rate limit exceeded - close active sessions

⚠️  Dashboard will start but pentests WILL FAIL.
Fix the errors above before running scans.
```

### API Error Response

When attempting to start a scan with validation failures:

```bash
POST /api/targets/1/scan

# Response: HTTP 503
{
  "detail": {
    "message": "System validation failed - pentests cannot run",
    "errors": [
      "GITHUB_TOKEN appears to be a placeholder",
      "Browserbase rate limit exceeded"
    ],
    "warnings": [],
    "help": "Fix the errors listed above. Check .env file and API keys."
  }
}
```

## Browserbase Rate Limit Handling

### Problem
Browserbase free tier has low concurrent session limits (1 session), causing rate limit errors.

### Solution
The new Browserbase client handles this gracefully:

1. **Session Reuse** - Reuses the same session for multiple screenshots within 5 minutes
2. **Retry with Backoff** - Automatically retries 3 times with increasing delays
3. **Explicit Logging** - Clearly logs rate limit errors:
   ```
   🚫 Browserbase rate limit exceeded!
      Error code: 429 - You've exceeded your max concurrent sessions
   ⏳ Waiting 5s before retry...
   ```
4. **Automatic Cleanup** - Closes sessions after use and on program exit
5. **Graceful Degradation** - Pentests continue without screenshots if Browserbase fails

### Manual Session Cleanup

```bash
# Via Python
python3 -c "from mcp.browserbase_client import close_all_sessions; close_all_sessions()"

# Or restart the dashboard (auto-cleanup on exit)
```

## GitHub Token Issues

### Problem
GitHub API was failing with "Needs token" or "Bad credentials" errors.

### Root Causes Fixed:

1. **Placeholder Detection** - Token like `ghp_xxxxxxxxxxxx` is now detected and rejected immediately
2. **Environment Loading** - Added `load_dotenv()` to ensure token is loaded
3. **Validation on Import** - Client validates token when module is imported
4. **Scope Verification** - Checks for required `repo` and `workflow` scopes
5. **Permission Checks** - Verifies write access to repository

### Generate Valid Token:

1. Visit: https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Required scopes:
   - ✅ `repo` (full control of private repositories)
   - ✅ `workflow` (update GitHub Action workflows)
4. Copy token immediately (shown only once)
5. Update `.env`:
   ```bash
   GITHUB_TOKEN=ghp_your_real_token_here
   GITHUB_REPO=username/repository
   ```

## Error Messages Reference

### GitHub Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `GITHUB_TOKEN not set` | Missing env var | Add `GITHUB_TOKEN` to `.env` |
| `Token is placeholder` | Example token | Replace with real token |
| `Bad credentials (401)` | Invalid/expired token | Generate new token |
| `Repository not found (404)` | Wrong repo name or no access | Check `GITHUB_REPO` format |
| `Access forbidden (403)` | Missing scopes | Regenerate token with `repo` scope |
| `No write permissions` | Read-only access | Grant push access or use different repo |

### Browserbase Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `Browserbase not configured` | Missing API key | Add `BROWSERBASE_API_KEY` to `.env` |
| `Rate limit exceeded (429)` | Too many concurrent sessions | Wait or upgrade plan |
| `Authentication failed (401)` | Invalid API key | Check `BROWSERBASE_API_KEY` |
| `Project ID invalid (404)` | Wrong project ID | Check `BROWSERBASE_PROJECT_ID` |

### E2B Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `E2B_API_KEY not set` | Missing env var | Add `E2B_API_KEY` to `.env` |
| `Sandbox creation failed` | Invalid API key or quota exceeded | Check API key and E2B plan |

### xAI Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `XAI_API_KEY not set` | Missing env var | Add `XAI_API_KEY` to `.env` |
| `API returned 401` | Invalid API key | Check xAI API key |
| `API returned 429` | Rate limit exceeded | Wait or upgrade plan |

## Architecture Changes

### Before (Silent Failures)
```
Dashboard → Start Scan → Agent Pipeline → ???
                                          ↓
                                    (fails silently)
                                          ↓
                                    (no feedback)
```

### After (Fail-Fast)
```
Dashboard Startup → Validation
                        ↓
                   ✅ Pass / ❌ Fail
                        ↓
        ┌───────────────┴───────────────┐
        ↓                               ↓
    ✅ Allow Scans              ❌ Block Scans
        ↓                               ↓
  Start Scan                    HTTP 503 Error
        ↓                        with detailed
  Agent Pipeline                 error message
```

### New Validation Flow

```
startup_validation.py
    ↓
┌───┴────────────────────────────────────┐
│ 1. Environment Variables               │
│ 2. GitHub API (with token validation) │
│ 3. Browserbase (with rate limit check)│
│ 4. E2B Sandbox                         │
│ 5. xAI Grok API                        │
│ 6. MCP Modules                         │
└───┬────────────────────────────────────┘
    ↓
validation_status = {
  is_valid: true/false,
  errors: [],
  warnings: []
}
    ↓
Dashboard API (/api/validation)
    ↓
POST /api/targets/{id}/scan
    ↓
check_system_ready()
    ↓
✅ Allow / ❌ HTTP 503
```

## API Changes

### New Endpoints

#### `GET /api/validation`
Returns current validation status:

```json
{
  "validated": true,
  "is_valid": true,
  "errors": [],
  "warnings": ["Browserbase not configured (optional)"],
  "timestamp": "2025-11-24T19:45:00.000Z"
}
```

### Modified Endpoints

#### `POST /api/targets/{id}/scan`
Now includes pre-scan validation:
- ✅ Returns scan object if validation passes
- ❌ Returns HTTP 503 with error details if validation fails

## Testing

### Test Validation

```bash
# Test all validations
python3 startup_validation.py

# Test specific components
python3 -c "from startup_validation import StartupValidator; import asyncio; v = StartupValidator(); asyncio.run(v.validate_github_auth())"
```

### Test Browserbase Session Management

```python
from mcp.browserbase_client import get_client

# Get client
client = get_client()

# Create session (with reuse)
session = client.create_session(reuse=True)
print(f"Session: {session.id if session else 'Failed'}")

# Take screenshot
if session:
    url = client.screenshot(session.id, "https://example.com")
    print(f"Screenshot: {url}")

# Cleanup
client.close_all_sessions()
```

### Test GitHub Token

```python
from mcp.github_client import get_client

try:
    client = get_client()
    repo = client.get_repo()
    print(f"✅ GitHub OK: {repo.name}")
except Exception as e:
    print(f"❌ GitHub Error: {e}")
```

## Migration Guide

### For Existing Installations

1. **Pull latest changes**:
   ```bash
   git pull origin master
   ```

2. **Verify .env configuration**:
   ```bash
   # Ensure all variables are set
   cat .env
   ```

3. **Replace placeholder tokens**:
   ```bash
   # Generate real GitHub token
   # Update GITHUB_TOKEN in .env
   ```

4. **Run validation**:
   ```bash
   python3 startup_validation.py
   ```

5. **Fix any errors** reported by validation

6. **Restart dashboard**:
   ```bash
   ./start-dashboard.sh
   ```

### For New Installations

Follow the standard setup, validation runs automatically:

```bash
# Setup .env
cp .env.example .env
nano .env  # Add real API keys

# Start dashboard (validation runs automatically)
./start-dashboard.sh
```

## Troubleshooting

### "Pentests not running"

**Check validation status**:
```bash
curl http://localhost:8000/api/validation
```

**Review errors** in response and fix them

### "Browserbase rate limit"

**Option 1 - Wait**:
Close active sessions and wait 5 minutes

**Option 2 - Disable screenshots**:
Remove `BROWSERBASE_API_KEY` from `.env` (pentests will still work)

**Option 3 - Upgrade**:
Contact Browserbase support to increase concurrent session limit

### "GitHub token invalid"

1. Generate new token at https://github.com/settings/tokens
2. Ensure scopes include `repo` and `workflow`
3. Update `GITHUB_TOKEN` in `.env`
4. Restart dashboard

## Related Documentation

- [DIAGNOSTICS.md](DIAGNOSTICS.md) - Full system diagnostic tool
- [MCP_ARCHITECTURE.md](MCP_ARCHITECTURE.md) - MCP client architecture
- [CLAUDE.md](CLAUDE.md) - Project overview

---

**Last Updated**: 2025-11-24
**Version**: 2.0 - Fail-Fast Error Handling
