#!/bin/bash

# Add environment variables to Vercel
# This script adds all required environment variables for AutoCTF

export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
nvm use 18

echo "Adding environment variables to Vercel..."
echo ""

# E2B_API_KEY
echo "Adding E2B_API_KEY..."
printf "e2b_be51ea2922aa3dcb736593879200bf8189245f9c\ny\n" | vercel env add E2B_API_KEY production

# OPENAI_API_KEY
echo "Adding OPENAI_API_KEY..."
printf "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\ny\n" | vercel env add OPENAI_API_KEY production

# BROWSERBASE_API_KEY
echo "Adding BROWSERBASE_API_KEY..."
printf "bb_live_EjpkdU6SEPtQ2dQ2skYSptTUNH0\ny\n" | vercel env add BROWSERBASE_API_KEY production

# BROWSERBASE_PROJECT_ID
echo "Adding BROWSERBASE_PROJECT_ID..."
printf "cf8f19b3-2d22-4323-a488-4f0e01c77f83\ny\n" | vercel env add BROWSERBASE_PROJECT_ID production

# GITHUB_TOKEN
echo "Adding GITHUB_TOKEN..."
printf "ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxx\ny\n" | vercel env add GITHUB_TOKEN production

# GITHUB_REPO
echo "Adding GITHUB_REPO..."
printf "AgentMulder404/autocTF\ny\n" | vercel env add GITHUB_REPO production

# DATABASE_URL
echo "Adding DATABASE_URL..."
printf "postgresql://neondb_owner:npg_1Fm6NtAzTcGw@ep-square-morning-afrdajqj-pooler.c-2.us-west-2.aws.neon.tech/neondb?sslmode=require\ny\n" | vercel env add DATABASE_URL production

echo ""
echo "✅ All environment variables added!"
echo ""
echo "Redeploying to production..."
vercel redeploy --prod --yes
