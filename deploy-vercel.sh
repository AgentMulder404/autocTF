#!/bin/bash

# AutoCTF Vercel Deployment Script
# This script helps deploy the dashboard to Vercel

set -e

echo "🚀 AutoCTF Vercel Deployment"
echo "=============================="
echo ""

# Check if vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    echo "❌ Vercel CLI not found. Installing..."
    npm install -g vercel
fi

echo "✅ Vercel CLI found"
echo ""

# Check if user is logged in
echo "Checking Vercel authentication..."
if ! vercel whoami &> /dev/null; then
    echo "📝 Please log in to Vercel:"
    vercel login
else
    echo "✅ Already logged in to Vercel"
fi
echo ""

# Deploy to Vercel
echo "🚀 Deploying to Vercel..."
echo "This will deploy your dashboard to production."
echo ""
echo "Important: Make sure you've set up environment variables in Vercel:"
echo "  - E2B_API_KEY"
echo "  - OPENAI_API_KEY"
echo "  - BROWSERBASE_API_KEY"
echo "  - BROWSERBASE_PROJECT_ID"
echo "  - GITHUB_TOKEN"
echo "  - GITHUB_REPO"
echo "  - DATABASE_URL"
echo ""
read -p "Have you set up environment variables in Vercel? (y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "Please set up environment variables first:"
    echo "  1. Visit https://vercel.com/dashboard"
    echo "  2. Select your project"
    echo "  3. Go to Settings > Environment Variables"
    echo "  4. Add all required variables"
    echo ""
    echo "Or use the CLI:"
    echo "  vercel env add E2B_API_KEY"
    echo "  vercel env add OPENAI_API_KEY"
    echo "  vercel env add BROWSERBASE_API_KEY"
    echo "  vercel env add BROWSERBASE_PROJECT_ID"
    echo "  vercel env add GITHUB_TOKEN"
    echo "  vercel env add GITHUB_REPO"
    echo "  vercel env add DATABASE_URL"
    echo ""
    exit 1
fi

# Deploy
echo ""
echo "Deploying to production..."
vercel --prod

echo ""
echo "✅ Deployment complete!"
echo ""
echo "Next steps:"
echo "  1. Visit your deployment URL"
echo "  2. Test the dashboard functionality"
echo "  3. Import a GitHub repository to test the new feature"
echo ""
