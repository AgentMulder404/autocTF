# Dashboard Connectivity Fix

**Date**: 2025-11-25
**Issue**: Frontend cannot connect to backend - "Cannot connect to AutoCTF API"

---

## 🔍 Root Cause Analysis

### Issue Traced Through Full Stack:

1. **Startup Script** (`start-dashboard.sh:15`):
   - ❌ Used `python main.py` instead of `python3`
   - ❌ System only has `python3` executable, not `python`
   - ❌ Backend never started, failing silently

2. **Backend Configuration** (`main.py:641`):
   - ✅ Already configured with `host="0.0.0.0"` and `port=8000`
   - ✅ CORS already configured with `allow_origins=["*"]`
   - ✅ Health check endpoint exists at `/`
   - ⚠️  No detailed health status endpoint

3. **Frontend Configuration** (`api.js:3`):
   - ✅ Correct API base: `http://localhost:8000`
   - ✅ Vite proxy configured for `/api` routes
   - ❌ No health check polling
   - ❌ No visible connection status

### Problems Identified:

- **Silent startup failure**: Script used `python` but system has `python3`
- **No health monitoring**: Frontend couldn't detect backend unavailability
- **No status display**: Users couldn't see connection status
- **Poor debugging**: No way to diagnose connectivity issues

---

## ✅ Fixes Implemented

### 1. Startup Script (`start-dashboard.sh`)

**Changes**:
- ✅ Changed `python` → `python3` (line 15)
- ✅ Changed `pip` → `pip3` (line 14)

**Before**:
```bash
pip install -q -r requirements.txt
python main.py &
```

**After**:
```bash
pip3 install -q -r requirements.txt
python3 main.py &
```

---

### 2. Enhanced Health Check Endpoint (`dashboard/backend/main.py`)

**New Endpoint**: `GET /api/health`

**Returns**:
```json
{
  "status": "healthy" | "degraded",
  "timestamp": "2025-11-25T04:36:21.574048",
  "version": "1.0.0",
  "api": "running",
  "database": "connected" | "error: ...",
  "validation": {
    "completed": true,
    "valid": false,
    "error_count": 0,
    "warning_count": 0
  }
}
```

**Features**:
- Database connectivity test with SQLAlchemy text()
- Validation status from startup
- Degraded status if validation failed or DB error
- Timestamp for monitoring
- Version info

**Code Added** (lines 129-162):
```python
@app.get("/api/health")
def health_check(db: Session = Depends(get_db)):
    """
    Comprehensive health check endpoint
    Returns database connectivity, validation status, and system info
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "api": "running",
        "database": "unknown",
        "validation": {
            "completed": validation_status.get("validated", False),
            "valid": validation_status.get("is_valid", False),
            "error_count": len(validation_status.get("errors", [])),
            "warning_count": len(validation_status.get("warnings", []))
        }
    }

    # Check database connectivity
    try:
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
        health_status["database"] = "connected"
    except Exception as e:
        health_status["database"] = f"error: {str(e)}"
        health_status["status"] = "degraded"

    # Check if system is ready for operations
    if not validation_status.get("is_valid", False):
        health_status["status"] = "degraded"

    return health_status
```

---

### 3. Frontend Health Check API (`dashboard/frontend/src/lib/api.js`)

**New Function** (lines 9-13):
```javascript
// Health check
export const checkHealth = async () => {
  const { data } = await api.get('/api/health');
  return data;
};
```

---

### 4. Connection Status Component (`dashboard/frontend/src/components/ConnectionStatus.jsx`)

**New File**: Complete real-time connection monitoring component

**Features**:
- ✅ Auto-polls health endpoint every 30 seconds
- ✅ Shows connection status with colored icons:
  - 🟢 Green: Connected (status === 'healthy')
  - 🟡 Yellow: Degraded (validation failed or DB issues)
  - 🔴 Red: Disconnected (cannot reach backend)
  - ⚪ Gray: Checking... (initial state)
- ✅ Shows database and validation status
- ✅ Shows error messages when disconnected
- ✅ Updates automatically without page refresh

**Code** (95 lines):
```javascript
import { useState, useEffect } from 'react';
import { Wifi, WifiOff, AlertCircle } from 'lucide-react';
import { checkHealth } from '../lib/api';

export default function ConnectionStatus() {
  const [status, setStatus] = useState('checking');
  const [health, setHealth] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    const checkConnection = async () => {
      try {
        const healthData = await checkHealth();
        setHealth(healthData);
        setStatus(healthData.status === 'healthy' ? 'connected' : 'degraded');
        setError(null);
      } catch (err) {
        setStatus('disconnected');
        setError(err.message || 'Cannot connect to backend');
        setHealth(null);
      }
    };

    // Check immediately
    checkConnection();

    // Then check every 30 seconds
    const interval = setInterval(checkConnection, 30000);

    return () => clearInterval(interval);
  }, []);

  // ... rendering logic
}
```

---

### 5. Layout Integration (`dashboard/frontend/src/components/Layout.jsx`)

**Changes**:
- ✅ Added `ConnectionStatus` import (line 3)
- ✅ Changed sidebar to flex column layout (line 18)
- ✅ Added `flex-1` to nav for spacing (line 27)
- ✅ Added `<ConnectionStatus />` at bottom of sidebar (line 50)

**Before**:
```jsx
<aside className="w-64 bg-gray-900 text-white">
  <div className="p-6">...</div>
  <nav className="mt-6">...</nav>
</aside>
```

**After**:
```jsx
<aside className="w-64 bg-gray-900 text-white flex flex-col">
  <div className="p-6">...</div>
  <nav className="mt-6 flex-1">...</nav>
  {/* Connection Status at bottom */}
  <ConnectionStatus />
</aside>
```

---

## 🧪 Testing

### Test 1: Backend Startup

```bash
cd /Users/kevinmello/Hackathon/autocTF

# Clean start
./start-dashboard.sh
```

**Expected Output**:
```
🚀 Starting AutoCTF Enterprise Dashboard...
📦 Starting backend API...
[Backend starts successfully]
🎨 Starting frontend...
[Frontend starts successfully]

✅ Dashboard started!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 Dashboard: http://localhost:3000
🔌 API Docs:  http://localhost:8000/docs
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**Verify Backend**:
```bash
curl http://localhost:8000/
# Expected: {"message":"AutoCTF Dashboard API","status":"running"}

curl http://localhost:8000/api/health | python3 -m json.tool
# Expected: Full health status JSON
```

---

### Test 2: Health Endpoint

```bash
curl -s http://localhost:8000/api/health | python3 -m json.tool
```

**Expected (Healthy)**:
```json
{
    "status": "healthy",
    "timestamp": "2025-11-25T04:36:21.574048",
    "version": "1.0.0",
    "api": "running",
    "database": "connected",
    "validation": {
        "completed": true,
        "valid": true,
        "error_count": 0,
        "warning_count": 0
    }
}
```

**Expected (Degraded - Validation Failed)**:
```json
{
    "status": "degraded",
    "timestamp": "2025-11-25T04:36:21.574048",
    "version": "1.0.0",
    "api": "running",
    "database": "connected",
    "validation": {
        "completed": true,
        "valid": false,
        "error_count": 2,
        "warning_count": 0
    }
}
```

---

### Test 3: Frontend Connection Status

1. **Open Dashboard**: http://localhost:3000
2. **Check Sidebar**: Look at bottom-left corner
3. **Expected Display**:
   - 🟢 **"API Connected"** (green) if backend healthy
   - 🟡 **"API Degraded"** (yellow) if validation failed
   - 🔴 **"API Offline"** (red) if backend down
   - Shows: `DB: ✓ • Val: ✓` or `DB: ✓ • Val: ✗`

**Test Scenarios**:

#### Scenario A: Backend Running & Healthy
1. Backend running with valid config
2. Status shows: 🟢 "API Connected"
3. Sub-status: `DB: ✓ • Val: ✓`

#### Scenario B: Backend Running but Validation Failed
1. Backend running with placeholder GITHUB_TOKEN
2. Status shows: 🟡 "API Degraded"
3. Sub-status: `DB: ✓ • Val: ✗`

#### Scenario C: Backend Down
1. Stop backend: `lsof -ti:8000 | xargs kill`
2. Wait 30 seconds (or refresh page)
3. Status shows: 🔴 "API Offline"
4. Error message: "Cannot connect to backend"

#### Scenario D: Backend Restarts
1. Start backend again
2. Wait up to 30 seconds
3. Status automatically updates to 🟢 or 🟡

---

### Test 4: GitHub Import (End-to-End)

**Prerequisites**: Backend must be running

```bash
# Test from command line
curl -X POST http://localhost:8000/api/targets/from-github \
  -H "Content-Type: application/json" \
  -d '{"github_url": "https://github.com/WebGoat/WebGoat"}'
```

**Expected (Success)**:
```json
{
  "id": 1,
  "name": "WebGoat/WebGoat",
  "url": "http://localhost:3000",
  "github_repo": "https://github.com/WebGoat/WebGoat",
  "repo_owner": "WebGoat",
  "repo_name": "WebGoat",
  "status": "active",
  ...
}
```

**Test from Dashboard**:
1. Open http://localhost:3000/targets
2. Check connection status shows 🟢 "API Connected"
3. Click "Add Target" → "From GitHub"
4. Enter: `https://github.com/WebGoat/WebGoat`
5. Click "Import from GitHub"
6. ✅ Should import successfully (not "Cannot connect to API")

---

## 🐛 Debugging Guide

### Issue: "Cannot connect to AutoCTF API"

**Check 1: Is backend running?**
```bash
curl http://localhost:8000/
# Should return: {"message":"AutoCTF Dashboard API","status":"running"}
```

**If connection refused:**
```bash
# Check if backend process exists
ps aux | grep "python3.*main.py" | grep -v grep

# If not running, start it
cd dashboard/backend
python3 main.py
```

**Check 2: Is backend on correct port?**
```bash
# Check what's listening on 8000
lsof -i:8000

# Expected:
# Python   <PID>  user   ... (LISTEN)
```

**Check 3: Can frontend reach backend?**
```bash
# From frontend directory
curl http://localhost:8000/api/health

# If this works, check browser console (F12)
# Look for CORS errors or network errors
```

---

### Issue: Backend won't start

**Error**: `python: command not found`
**Fix**: Use `python3` instead of `python`
```bash
cd dashboard/backend
python3 main.py
```

**Error**: `Address already in use`
**Fix**: Kill existing backend process
```bash
lsof -ti:8000 | xargs kill -9
# Then restart backend
python3 main.py
```

**Error**: `ModuleNotFoundError: No module named 'fastapi'`
**Fix**: Install dependencies
```bash
pip3 install -r requirements.txt
```

---

### Issue: Connection Status Shows "API Degraded"

**Meaning**: Backend is running but validation failed

**Check validation status**:
```bash
curl http://localhost:8000/api/validation | python3 -m json.tool
```

**Common causes**:
- GITHUB_TOKEN is placeholder → Replace with real token
- DATABASE_URL invalid → Check Neon connection string
- Missing API keys → Check .env file

**Fix**: See `.env` configuration section below

---

## 📝 Configuration Reference

### Required Environment Variables

Create/update `.env` file in project root:

```bash
# Required for backend to start
E2B_API_KEY=e2b_xxxxx
GITHUB_TOKEN=ghp_xxxxx  # NOT ghp_xxxxxxxxxxxxxxxx
GITHUB_REPO=username/repository
XAI_API_KEY=xai-xxxxx
DATABASE_URL=postgresql://user:pass@host/db

# Optional (for full functionality)
BROWSERBASE_API_KEY=bb_live_xxxxx
BROWSERBASE_PROJECT_ID=xxxxx
OPENAI_API_KEY=sk-xxxxx
```

**IMPORTANT**: Replace all placeholder values with real API keys

---

### Backend Configuration

**File**: `dashboard/backend/main.py:641`
```python
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

**Host Binding**:
- `0.0.0.0` - Binds to all interfaces (works in Codespaces/E2B)
- `127.0.0.1` - Local only (won't work in containers)

**Port**:
- Default: `8000`
- Change if port conflict occurs

**CORS**:
- Configured at `main.py:52-58`
- Currently allows all origins: `allow_origins=["*"]`
- For production, restrict to specific domains

---

### Frontend Configuration

**API Base URL**: `dashboard/frontend/src/lib/api.js:3`
```javascript
const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';
```

**To override** (optional):
Create `dashboard/frontend/.env`:
```
VITE_API_URL=http://different-host:8000
```

**Vite Proxy**: `dashboard/frontend/vite.config.js:8-13`
```javascript
server: {
  port: 3000,
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true,
    }
  }
}
```

---

## 🎯 Success Criteria

Your AutoCTF dashboard has working connectivity when:

✅ **Backend Starts Successfully**:
```bash
$ cd dashboard/backend && python3 main.py
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

✅ **Health Endpoint Responds**:
```bash
$ curl http://localhost:8000/api/health
{"status":"healthy",...}
```

✅ **Frontend Shows Connected Status**:
- Open http://localhost:3000
- Bottom-left sidebar shows: 🟢 "API Connected"
- No "Cannot connect to AutoCTF API" errors

✅ **GitHub Import Works**:
- Navigate to Targets page
- Click "Add Target" → "From GitHub"
- Enter repo URL
- Successfully imports (doesn't show connection error)

✅ **Real-Time Monitoring Works**:
- Status updates automatically every 30 seconds
- Stop backend → Status turns red within 30s
- Start backend → Status turns green within 30s

---

## 📊 Changes Summary

| File | Type | Lines | Description |
|------|------|-------|-------------|
| `start-dashboard.sh` | Modified | 2 | Changed python→python3, pip→pip3 |
| `dashboard/backend/main.py` | Modified | +38 | Added `/api/health` endpoint |
| `dashboard/frontend/src/lib/api.js` | Modified | +5 | Added `checkHealth()` function |
| `dashboard/frontend/src/components/ConnectionStatus.jsx` | New | 95 | Connection status monitoring component |
| `dashboard/frontend/src/components/Layout.jsx` | Modified | +4 | Integrated ConnectionStatus in sidebar |

**Total**: 144 lines added/modified across 5 files

---

## 🚀 Quick Start Commands

### Start Everything (Recommended)
```bash
cd /Users/kevinmello/Hackathon/autocTF
./start-dashboard.sh
```

### Start Backend Only
```bash
cd dashboard/backend
pip3 install -r requirements.txt
python3 main.py
```

### Start Frontend Only
```bash
cd dashboard/frontend
npm install  # first time only
npm run dev
```

### Test Connectivity
```bash
# Test backend
curl http://localhost:8000/

# Test health
curl http://localhost:8000/api/health

# Test targets API
curl http://localhost:8000/api/targets

# Open dashboard
open http://localhost:3000
```

### Stop Everything
```bash
# Kill backend
lsof -ti:8000 | xargs kill

# Kill frontend (if started separately)
lsof -ti:3000 | xargs kill
```

---

## 🔧 Troubleshooting Checklist

Before asking for help, verify:

1. ✅ Backend is running:
   ```bash
   curl http://localhost:8000/
   ```

2. ✅ Frontend is running:
   ```bash
   curl http://localhost:3000
   ```

3. ✅ Health endpoint responds:
   ```bash
   curl http://localhost:8000/api/health
   ```

4. ✅ Browser console shows no CORS errors (F12 → Console)

5. ✅ Connection status in sidebar shows current state

6. ✅ Environment variables are set in `.env`

7. ✅ Using `python3` not `python`

8. ✅ Ports 3000 and 8000 are not blocked

---

## 📞 Support

If issues persist after following this guide:

1. **Check Logs**:
   - Backend: Terminal where `python3 main.py` runs
   - Frontend: Browser console (F12)
   - Startup script: Terminal output

2. **Verify Health Status**:
   ```bash
   curl http://localhost:8000/api/health | python3 -m json.tool
   ```

3. **Check Validation**:
   ```bash
   curl http://localhost:8000/api/validation | python3 -m json.tool
   ```

4. **Review Documentation**:
   - [GITHUB_IMPORT_FIX.md](GITHUB_IMPORT_FIX.md) - Import issues
   - [IMPROVEMENTS_SUMMARY.md](IMPROVEMENTS_SUMMARY.md) - Validation issues
   - [STARTUP_VALIDATION.md](STARTUP_VALIDATION.md) - Environment setup

---

**Last Updated**: 2025-11-25
**Status**: ✅ FIXED - Backend now starts correctly and frontend shows connection status
