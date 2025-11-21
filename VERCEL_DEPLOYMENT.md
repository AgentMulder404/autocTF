# Vercel Deployment Guide

This guide will help you deploy the AutoCTF Dashboard to Vercel.

## Prerequisites

1. A Vercel account (sign up at https://vercel.com)
2. Vercel CLI installed: `npm install -g vercel`
3. Neon PostgreSQL database (already configured)

## Deployment Steps

### 1. Install Vercel CLI

```bash
npm install -g vercel
```

### 2. Login to Vercel

```bash
vercel login
```

### 3. Configure Environment Variables

Before deploying, you need to add your environment variables to Vercel:

```bash
vercel env add E2B_API_KEY
vercel env add OPENAI_API_KEY
vercel env add BROWSERBASE_API_KEY
vercel env add BROWSERBASE_PROJECT_ID
vercel env add GITHUB_TOKEN
vercel env add GITHUB_REPO
vercel env add DATABASE_URL
```

When prompted, enter the values from your `.env` file. Select "Production", "Preview", and "Development" for each variable.

**Important:** Your `DATABASE_URL` should be your Neon PostgreSQL connection string:
```
postgresql://user:password@ep-xxx.aws.neon.tech/neondb?sslmode=require
```

### 4. Deploy to Vercel

From the project root directory:

```bash
# First deployment (will prompt for configuration)
vercel

# Or deploy directly to production
vercel --prod
```

### 5. Verify Deployment

After deployment, Vercel will provide a URL (e.g., `https://autoctf-xxx.vercel.app`).

Test the deployment:
- Visit the dashboard: `https://your-deployment.vercel.app`
- Check API health: `https://your-deployment.vercel.app/api`
- View API docs: `https://your-deployment.vercel.app/api/docs`

## Configuration Files

The following files configure the Vercel deployment:

- `vercel.json` - Main Vercel configuration
- `api/index.py` - Serverless function entry point for FastAPI backend
- `api/requirements.txt` - Python dependencies for serverless function
- `.vercelignore` - Files to exclude from deployment

## Architecture

### Frontend (Static Site)
- Built with Vite
- Deployed as static files from `dashboard/frontend/dist`
- Served directly from Vercel's CDN

### Backend (Serverless Functions)
- FastAPI application wrapped with Mangum
- Deployed as Python serverless function at `/api`
- Auto-scales based on traffic
- Cold start time: ~2-3 seconds

### Database
- Neon PostgreSQL (cloud-hosted)
- Persistent across deployments
- No setup needed (already configured)

## Updating the Deployment

After making code changes:

```bash
# Push changes to git
git add .
git commit -m "Your changes"
git push

# Deploy to Vercel
vercel --prod
```

Or connect your GitHub repo to Vercel for automatic deployments:
1. Go to https://vercel.com/dashboard
2. Click "Import Project"
3. Select your GitHub repository
4. Vercel will auto-deploy on every push to main

## Troubleshooting

### Build Fails

Check the build logs in Vercel dashboard:
```bash
vercel logs
```

### Backend API Not Working

1. Verify environment variables are set:
   ```bash
   vercel env ls
   ```

2. Check serverless function logs:
   ```bash
   vercel logs --follow
   ```

3. Ensure `DATABASE_URL` includes `?sslmode=require`

### Frontend Can't Connect to API

The frontend automatically uses relative URLs (`/api/*`) which Vercel rewrites to the serverless function. No additional configuration needed.

## Performance Considerations

- **Cold Starts**: First request after idle period takes 2-3 seconds
- **Connection Pooling**: Configured in `database.py` (5 connections, max 10)
- **Serverless Timeout**: 10 seconds default (can be increased in Vercel Pro)
- **Long-Running Tasks**: Consider using background workers for pentests > 10s

## Cost Estimate

- **Vercel Free Tier**:
  - 100 GB bandwidth
  - Serverless function executions: 100 GB-hours
  - Usually sufficient for development/small teams

- **Vercel Pro ($20/month)**:
  - 1 TB bandwidth
  - Extended function timeout (60s)
  - Better for production use

- **Neon Free Tier**:
  - 3 GB storage
  - 0.5 GB RAM
  - Sufficient for moderate usage

## Security Notes

- All API routes are public by default
- Add authentication middleware in `main.py` for production
- Enable CORS restrictions in `main.py` (currently set to `["*"]`)
- Rotate API keys regularly
- Use Vercel's environment variable encryption

## Next Steps

1. Deploy to Vercel: `vercel --prod`
2. Test all features on the live site
3. Set up automatic deployments via GitHub
4. Configure custom domain (optional)
5. Add authentication (recommended for production)
