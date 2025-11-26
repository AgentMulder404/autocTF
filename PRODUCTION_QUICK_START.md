# AutoCTF Production Quick Start

**TL;DR**: Your project is now ready for production deployment on Railway + Trigger.dev + Vercel.

## ✅ What Was Done

### 1. Railway Backend Configuration
- **File**: `dashboard/backend/main_production.py`
- **Features**:
  - Health check endpoint: `/health`
  - SSE streaming: `/api/runs/{id}/stream`
  - Internal endpoints for Trigger.dev
  - API key authentication
  - CORS configured for Vercel

### 2. Trigger.dev Job Queue
- **Directory**: `trigger/`
- **Job**: `pentest-scan` - Handles 2-10+ minute scans
- **Features**:
  - TypeScript job definitions
  - Real-time progress updates
  - 30-minute timeout
  - Retry logic

### 3. Deployment Configs
- `railway.json` - Railway build config
- `Procfile` - Process definition
- `nixpacks.toml` - Build configuration
- `.env.production.example` - All env vars

### 4. Documentation
- `DEPLOYMENT.md` - Complete step-by-step guide
- Environment variable reference
- Troubleshooting section

---

## 🚀 Deploy in 15 Minutes

### Step 1: Railway (5 min)
```bash
# Install Railway CLI
brew install railway

# Initialize project
cd /path/to/autocTF
railway init

# Set environment variables
railway variables set E2B_API_KEY=your_key
railway variables set XAI_API_KEY=your_key
railway variables set DATABASE_URL=your_neon_url
railway variables set BACKEND_API_KEY=$(openssl rand -hex 32)

# Deploy
railway up

# Get your Railway URL
railway domain
```

### Step 2: Trigger.dev (5 min)
```bash
# Install dependencies
cd trigger/
npm install

# Set API key
echo "TRIGGER_API_KEY=your_trigger_key" > .env

# Deploy jobs
npm run deploy

# Verify
npx @trigger.dev/cli list
```

### Step 3: Vercel (5 min)
```bash
# Install Vercel CLI
npm install -g vercel

# Configure frontend
cd dashboard/frontend/
echo "VITE_API_URL=https://your-railway-domain.railway.app" > .env.production

# Deploy
vercel --prod

# Get Vercel URL
vercel domains ls
```

### Step 4: Connect Everything
```bash
# Add Vercel URL to Railway CORS
railway variables set FRONTEND_URL=https://your-vercel-domain.vercel.app

# Redeploy Railway
railway up
```

**Done!** ✨

---

## 📋 Key Changes from Dev to Production

| Feature | Development | Production |
|---------|-------------|------------|
| **Backend** | Local `main.py` | Railway `main_production.py` |
| **Jobs** | BackgroundTasks | Trigger.dev queue |
| **Real-time** | Polling | Server-Sent Events (SSE) |
| **Frontend** | Localhost:3000 | Vercel CDN |
| **Timeouts** | No limit | Trigger.dev handles long jobs |

---

## 🔧 Using main_production.py

### Option 1: Swap Files (Recommended)
```bash
cd dashboard/backend/

# Backup original
mv main.py main_dev.py

# Use production version
mv main_production.py main.py

# Deploy to Railway
railway up
```

### Option 2: Environment-based Loading
```bash
# Keep both files, use env var to switch
if os.getenv("RAILWAY_ENVIRONMENT"):
    from main_production import app
else:
    from main import app
```

---

## 🧪 Testing Production Locally

### Start Railway Backend Locally
```bash
cd dashboard/backend/

# Use production environment
export PORT=8000
export BACKEND_API_KEY=test-key
export RAILWAY_PUBLIC_URL=http://localhost:8000
export TRIGGER_API_KEY=your_trigger_key

# Run production backend
python main_production.py
```

### Test SSE Endpoint
```bash
# Test Server-Sent Events
curl -N http://localhost:8000/api/runs/1/stream

# Expected: Stream of events
# data: {"status":"connected","runId":1}
# : heartbeat
```

### Test Internal Endpoints
```bash
# Test recon endpoint (requires API key)
curl -X POST http://localhost:8000/internal/run-recon \
  -H "X-API-Key: test-key" \
  -H "Content-Type: application/json" \
  -d '{"runId":1,"targetUrl":"http://testphp.vulnweb.com"}'
```

---

## 🔐 Security Checklist

- [ ] Generate secure `BACKEND_API_KEY` (32+ chars)
- [ ] Update CORS to specific Vercel domain (remove `*`)
- [ ] Enable Railway authentication (Pro plan)
- [ ] Rotate API keys every 90 days
- [ ] Add rate limiting middleware
- [ ] Enable Vercel Edge Firewall
- [ ] Set up monitoring (Sentry, LogRocket)

---

## 📊 Monitoring Your Deployment

### Railway
- Dashboard: https://railway.app/project/your-project
- Logs: `railway logs`
- Metrics: CPU, memory, network

### Trigger.dev
- Dashboard: https://cloud.trigger.dev/projects/your-project
- Job runs: View execution history
- Errors: Failed job details

### Vercel
- Dashboard: https://vercel.com/your-project
- Analytics: Page views, performance
- Logs: Function execution logs

---

## 🐛 Common Issues

### "Trigger.dev job not running"
```bash
# Check Trigger.dev dashboard
open https://cloud.trigger.dev/projects/your-project/runs

# Verify API key
npx @trigger.dev/cli whoami

# Check Railway logs
railway logs | grep "Queueing pentest"
```

### "SSE connection closed immediately"
```bash
# Verify SSE endpoint
curl -N https://your-railway-domain.railway.app/api/runs/1/stream

# Check Railway logs for errors
railway logs | grep SSE

# Common fix: Disable Railway proxy buffering
# Add to railway.json: "proxy": {"buffering": false}
```

### "Frontend can't connect to backend"
```bash
# Test CORS
curl -H "Origin: https://your-vercel-domain.vercel.app" \
  -H "Access-Control-Request-Method: POST" \
  -X OPTIONS \
  https://your-railway-domain.railway.app/api/targets

# Expected: CORS headers in response
# Access-Control-Allow-Origin: https://your-vercel-domain.vercel.app
```

---

## 💰 Cost Breakdown

### Free Tier (Hobby Projects)
- **Railway**: $5 credit/month (enough for ~200 hours)
- **Trigger.dev**: 1M runs/month free
- **Vercel**: Unlimited deployments
- **Neon**: 3 projects, 10GB storage
- **E2B**: 100 hours/month

**Total**: ~$0-5/month

### Production (Pro Plans)
- **Railway Pro**: $20/month (no sleep, more resources)
- **Trigger.dev Pro**: $20/month (priority queuing)
- **Vercel Pro**: $20/month (team features)
- **Neon Scale**: $19/month (autoscaling)
- **E2B**: $10/100 hours

**Total**: ~$80-100/month

---

## 📚 Additional Resources

- **Railway Docs**: https://docs.railway.app
- **Trigger.dev Docs**: https://trigger.dev/docs
- **Vercel Docs**: https://vercel.com/docs
- **Full Deployment Guide**: See `DEPLOYMENT.md`
- **Environment Variables**: See `.env.production.example`

---

## 🆘 Need Help?

1. Check `DEPLOYMENT.md` for detailed instructions
2. Review Railway/Trigger.dev/Vercel logs
3. Open an issue: https://github.com/AgentMulder404/autocTF/issues
4. Join Discord: [Add your Discord link]

---

**Your AutoCTF production deployment is ready to go!** 🚀

Next step: Follow `DEPLOYMENT.md` for complete deployment instructions.
