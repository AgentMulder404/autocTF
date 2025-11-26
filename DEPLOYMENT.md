# AutoCTF Production Deployment Guide

Complete guide for deploying AutoCTF to production using **Railway** (backend), **Trigger.dev** (jobs), and **Vercel** (frontend).

## Architecture Overview

```
┌─────────────────┐
│  Vercel Frontend│ (React)
│  Port: 3000     │
└────────┬────────┘
         │ API Calls
         ▼
┌─────────────────┐      ┌──────────────────┐
│ Railway Backend │◄────►│  Trigger.dev     │
│  FastAPI        │ Jobs │  Background Jobs │
│  Port: 8000     │      │  (Pentest Scans) │
└────────┬────────┘      └──────────────────┘
         │
         ▼
┌─────────────────┐      ┌──────────────────┐
│ Neon PostgreSQL │      │  E2B Sandboxes   │
│  Database       │      │  Security Scans  │
└─────────────────┘      └──────────────────┘
```

### Why This Stack?

| Service | Purpose | Why Not Vercel? |
|---------|---------|-----------------|
| **Railway** | Backend API | Supports long-running processes, background workers |
| **Trigger.dev** | Job Queue | Handles 2-10+ minute pentest scans without timeouts |
| **Vercel** | Frontend | Perfect for React, CDN, automatic deployments |
| **Neon** | Database | Serverless PostgreSQL, no maintenance |
| **E2B** | Sandboxes | Cloud execution for security tools |

**The Problem**: Vercel has a **10-second** function timeout for Hobby plan, **60 seconds** for Pro. Pentest scans take **2-10+ minutes**.

**The Solution**: Move long-running jobs to Trigger.dev, keep fast API endpoints on Railway.

---

## Prerequisites

### Required Accounts

1. **Railway** - https://railway.app (Backend hosting)
2. **Trigger.dev** - https://cloud.trigger.dev (Job queue)
3. **Vercel** - https://vercel.com (Frontend hosting)
4. **Neon** - https://neon.tech (PostgreSQL database)
5. **E2B** - https://e2b.dev/dashboard (Cloud sandboxes)
6. **xAI** - https://x.ai (Grok LLM API)

### Optional Accounts

- **GitHub** (for PR creation) - https://github.com/settings/tokens
- **Browserbase** (for screenshots) - https://browserbase.com

---

## Step 1: Deploy to Railway (Backend)

### 1.1 Install Railway CLI

```bash
# macOS
brew install railway

# Or use npm
npm install -g @railway/cli

# Login
railway login
```

### 1.2 Initialize Railway Project

```bash
cd /path/to/autocTF

# Initialize Railway
railway init

# Select "Create new project"
# Project name: autoctf-backend
```

### 1.3 Configure Environment Variables

```bash
# Set all required environment variables
railway variables set E2B_API_KEY=e2b_your_key
railway variables set XAI_API_KEY=xai-your_key
railway variables set DATABASE_URL=postgresql://user:pass@host/db
railway variables set BACKEND_API_KEY=$(openssl rand -hex 32)

# Optional variables
railway variables set GITHUB_TOKEN=ghp_your_token
railway variables set GITHUB_REPO=username/repo
railway variables set BROWSERBASE_API_KEY=bb_live_your_key
railway variables set BROWSERBASE_PROJECT_ID=your_project_id
```

**Generate secure BACKEND_API_KEY**:
```bash
# Linux/macOS
openssl rand -hex 32

# Or use Python
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### 1.4 Deploy to Railway

```bash
# Deploy backend
railway up

# Railway will:
# 1. Detect Python project (via railway.json)
# 2. Install dependencies (requirements.txt)
# 3. Start FastAPI server (uvicorn)
# 4. Generate public URL

# Get your Railway URL
railway domain

# Example: https://autoctf-production.up.railway.app
```

### 1.5 Set Railway URL

```bash
# Update RAILWAY_PUBLIC_URL with your actual domain
railway variables set RAILWAY_PUBLIC_URL=https://your-domain.up.railway.app
```

### 1.6 Verify Deployment

```bash
# Check health endpoint
curl https://your-domain.up.railway.app/health

# Expected response:
# {"status":"healthy","version":"2.0.0","services":{"database":"connected"}}

# Check API docs
open https://your-domain.up.railway.app/docs
```

---

## Step 2: Deploy Trigger.dev (Background Jobs)

### 2.1 Install Trigger.dev CLI

```bash
npm install -g @trigger.dev/cli

# Or use npx
npx @trigger.dev/cli@latest
```

### 2.2 Create Trigger.dev Project

1. Go to https://cloud.trigger.dev
2. Click "New Project"
3. Project name: `autoctf-pentest`
4. Copy your **API Key** (starts with `tr_dev_` or `tr_prod_`)

### 2.3 Configure Trigger.dev

```bash
cd trigger/

# Initialize Trigger.dev
npm install

# Create .env file
cat > .env <<EOF
TRIGGER_API_KEY=tr_dev_your_trigger_api_key
TRIGGER_API_URL=https://api.trigger.dev
EOF

# Set Railway backend URL in trigger jobs
# Edit trigger/src/jobs/pentest-scan.ts
# Update BACKEND_URL constant to your Railway domain
```

### 2.4 Deploy Trigger.dev Jobs

```bash
cd trigger/

# Deploy to Trigger.dev
npm run deploy

# Or use CLI
npx @trigger.dev/cli deploy

# Verify deployment
npx @trigger.dev/cli list
```

### 2.5 Test Trigger.dev Integration

```bash
# Test pentest job from Railway
curl -X POST https://your-railway-domain.up.railway.app/api/targets/1/scan \
  -H "Content-Type: application/json"

# Check Trigger.dev dashboard
open https://cloud.trigger.dev/projects/your-project/runs
```

---

## Step 3: Deploy to Vercel (Frontend)

### 3.1 Install Vercel CLI

```bash
npm install -g vercel

# Login
vercel login
```

### 3.2 Configure Frontend Environment

```bash
cd dashboard/frontend/

# Create production .env
cat > .env.production <<EOF
VITE_API_URL=https://your-railway-domain.up.railway.app
EOF
```

### 3.3 Deploy to Vercel

```bash
cd dashboard/frontend/

# Deploy
vercel

# Follow prompts:
# - Set up and deploy? Yes
# - Which scope? Your account
# - Link to existing project? No
# - Project name: autoctf-dashboard
# - Directory: ./
# - Override settings? No

# Deploy to production
vercel --prod

# Get your Vercel URL
# Example: https://autoctf-dashboard.vercel.app
```

### 3.4 Configure CORS on Railway

```bash
# Add Vercel URL to Railway CORS
railway variables set FRONTEND_URL=https://autoctf-dashboard.vercel.app

# Redeploy Railway to apply changes
railway up
```

### 3.5 Verify Frontend

```bash
# Open dashboard
open https://autoctf-dashboard.vercel.app

# Test API connection
# Go to Dashboard -> Check connection status indicator
```

---

## Step 4: Configure Real-time Updates (SSE)

### 4.1 Update Frontend to Use SSE

Create `dashboard/frontend/src/lib/sse.js`:

```javascript
export function subscribeToScanUpdates(runId, onUpdate) {
  const apiUrl = import.meta.env.VITE_API_URL;
  const eventSource = new EventSource(`${apiUrl}/api/runs/${runId}/stream`);

  eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data);
    onUpdate(data);
  };

  eventSource.onerror = (error) => {
    console.error('SSE connection error:', error);
    eventSource.close();
  };

  // Return cleanup function
  return () => eventSource.close();
}
```

### 4.2 Use SSE in Scan Component

Update `dashboard/frontend/src/pages/Scans.jsx`:

```javascript
import { subscribeToScanUpdates } from '../lib/sse';

function ScanDetail({ runId }) {
  const [progress, setProgress] = useState([]);

  useEffect(() => {
    const unsubscribe = subscribeToScanUpdates(runId, (update) => {
      setProgress(prev => [...prev, update]);
    });

    return unsubscribe; // Cleanup on unmount
  }, [runId]);

  return (
    <div>
      <h2>Scan Progress</h2>
      {progress.map((msg, i) => (
        <div key={i}>{msg.message}</div>
      ))}
    </div>
  );
}
```

---

## Step 5: Production Checklist

### Security

- [ ] Change `BACKEND_API_KEY` to secure random value
- [ ] Update CORS `allow_origins` to specific domains (remove `*`)
- [ ] Enable HTTPS only (Railway does this automatically)
- [ ] Rotate API keys regularly
- [ ] Add rate limiting (Railway middleware or Cloudflare)

### Monitoring

- [ ] Set up Railway metrics dashboard
- [ ] Monitor Trigger.dev job queue
- [ ] Set up error tracking (Sentry, LogRocket)
- [ ] Configure health check alerts

### Database

- [ ] Enable Neon connection pooling
- [ ] Set up automated backups (Neon does this automatically)
- [ ] Monitor database size and queries

### Performance

- [ ] Enable Railway autoscaling (Pro plan)
- [ ] Configure Trigger.dev concurrency limits
- [ ] Optimize frontend bundle size
- [ ] Enable Vercel Edge CDN

---

## Environment Variables Summary

### Railway Backend
```bash
# Required
E2B_API_KEY=e2b_xxx
XAI_API_KEY=xai-xxx
DATABASE_URL=postgresql://xxx
BACKEND_API_KEY=random-secure-key
RAILWAY_PUBLIC_URL=https://your-domain.railway.app
TRIGGER_API_KEY=tr_xxx
TRIGGER_API_URL=https://api.trigger.dev
FRONTEND_URL=https://your-app.vercel.app

# Optional
GITHUB_TOKEN=ghp_xxx
GITHUB_REPO=username/repo
BROWSERBASE_API_KEY=bb_live_xxx
BROWSERBASE_PROJECT_ID=xxx
```

### Trigger.dev Jobs
```bash
TRIGGER_API_KEY=tr_xxx
TRIGGER_API_URL=https://api.trigger.dev
```

### Vercel Frontend
```bash
VITE_API_URL=https://your-railway-domain.up.railway.app
```

---

## Troubleshooting

### Railway Backend Won't Start

```bash
# Check logs
railway logs

# Common issues:
# 1. Missing environment variables
railway variables

# 2. Database connection failed
# Verify DATABASE_URL is correct

# 3. Port binding issue
# Railway sets PORT automatically, don't hardcode
```

### Trigger.dev Jobs Not Running

```bash
# Check Trigger.dev dashboard
open https://cloud.trigger.dev/projects/your-project/runs

# Verify API key
npx @trigger.dev/cli whoami

# Test job manually
npx @trigger.dev/cli test pentest-scan --payload '{"runId":1}'
```

### Frontend Can't Reach Backend

```bash
# Check CORS configuration
curl -H "Origin: https://your-vercel-domain.vercel.app" \
  -H "Access-Control-Request-Method: POST" \
  -X OPTIONS \
  https://your-railway-domain.railway.app/api/targets

# Should return CORS headers
```

### SSE Not Working

```bash
# Test SSE endpoint
curl -N https://your-railway-domain.railway.app/api/runs/1/stream

# Should stream events
# If not, check Railway logs for errors
```

---

## Cost Estimation

### Free Tier Limits

| Service | Free Tier | Monthly Cost (if exceeded) |
|---------|-----------|---------------------------|
| **Railway** | $5 credit | $0.000231/GB-hour |
| **Trigger.dev** | 1M runs | $20/month Pro |
| **Vercel** | Unlimited | $20/month Pro |
| **Neon** | 3 projects | $19/month Scale |
| **E2B** | 100 hours | $10/100 hours |

**Estimated Monthly Cost**: $0-20 (free tier) or $50-100 (production)

---

## Next Steps

1. **Deploy to production** using this guide
2. **Test end-to-end** flow: Frontend → Railway → Trigger.dev → E2B
3. **Monitor** for 24 hours to catch any issues
4. **Scale** as needed (Railway Pro, Trigger.dev Pro)
5. **Add monitoring** (Sentry, LogRocket, Datadog)

---

## Support

- **Railway Docs**: https://docs.railway.app
- **Trigger.dev Docs**: https://trigger.dev/docs
- **Vercel Docs**: https://vercel.com/docs
- **AutoCTF Issues**: https://github.com/yourusername/autocTF/issues

---

**Deployment Complete!** 🚀

Your AutoCTF platform is now running in production with:
- ✅ Scalable backend (Railway)
- ✅ Long-running jobs (Trigger.dev)
- ✅ Fast frontend (Vercel)
- ✅ Real-time updates (SSE)
- ✅ Cloud sandboxes (E2B)
