# AutoCTF Dashboard Usage Guide

## Step 1: Access Your Dashboard

1. **Visit your deployment:**
   ```
   https://autoc-82o805vdh-kevinmello8-2597s-projects.vercel.app
   ```

2. **Sign in with Vercel:**
   - You'll see a "Vercel Authentication" page
   - Click to authenticate with your Vercel account
   - After authentication, you'll be redirected to the dashboard

## Step 2: Understand the Dashboard Layout

Once logged in, you'll see the main dashboard with these sections:

### Navigation Menu (Left Sidebar)
- **Dashboard** - Overview of all pentests and vulnerabilities
- **Targets** - Manage your target applications
- **Scans** - View all pentest runs and their status
- **Vulnerabilities** - Browse discovered security issues

## Step 3: Add Your First Target

You have **two options** to add targets:

### Option A: Import from GitHub (NEW!)

1. Click **"Targets"** in the sidebar
2. Click the **"GitHub"** tab at the top
3. Enter a GitHub repository URL:
   ```
   https://github.com/username/repo
   or
   git@github.com:username/repo.git
   ```
4. Click **"Import from GitHub"**
5. The system will automatically:
   - Extract the repository owner and name
   - Set the target URL
   - Add GitHub metadata for tracking

### Option B: Manual Entry

1. Click **"Targets"** in the sidebar
2. Click the **"Manual"** tab
3. Fill in the target details:
   - **Name**: e.g., "My Web App"
   - **URL**: e.g., "http://localhost:8080" or your app URL
   - **Description**: Brief description of the target
4. Click **"Add Target"**

## Step 4: Run a Penetration Test

1. Go to the **"Targets"** page
2. Find your target in the list
3. Click the **"Scan"** button next to the target
4. The pentest will start automatically

### What Happens During a Scan:
1. **Reconnaissance Phase**
   - Runs nmap (port scanning)
   - Runs gobuster (directory enumeration)
   - Runs nikto (web vulnerability scanning)

2. **Analysis Phase**
   - LLM analyzes scan results
   - Identifies potential vulnerabilities
   - Prioritizes findings

3. **Exploitation Phase**
   - Attempts to exploit confirmed vulnerabilities
   - Tests for SQL injection, XSS, etc.
   - Captures proof of exploitation

4. **Patching Phase**
   - Generates security patches
   - Creates a GitHub Pull Request
   - Documents findings and fixes

## Step 5: Monitor Scan Progress

1. Click **"Scans"** in the sidebar
2. You'll see all your pentest runs with statuses:
   - **Running** - Scan in progress
   - **Completed** - Scan finished successfully
   - **Failed** - Scan encountered an error

3. Click on a scan to view:
   - Detailed logs
   - Vulnerabilities found
   - Exploitation results
   - Generated patches

## Step 6: Review Vulnerabilities

1. Click **"Vulnerabilities"** in the sidebar
2. Browse all discovered vulnerabilities across all targets
3. Each vulnerability shows:
   - **Severity**: Critical, High, Medium, Low
   - **Type**: SQLi, XSS, CSRF, etc.
   - **Status**: Open, Fixed, False Positive
   - **Target**: Which application has the vulnerability
   - **Proof**: Evidence of the vulnerability

4. Click on a vulnerability to view:
   - Detailed description
   - Reproduction steps
   - Suggested fix
   - Related GitHub PR (if auto-patched)

## Step 7: View Dashboard Analytics

1. Click **"Dashboard"** in the sidebar
2. See overview statistics:
   - Total targets being monitored
   - Total scans performed
   - Vulnerabilities discovered
   - Auto-patched issues

3. View trend charts:
   - Vulnerability trends over time
   - Scan frequency
   - Fix rates

## Example Walkthrough

Let's add and scan a test target:

### Using the DVWA Test Target

1. **Add Target:**
   - Go to Targets → Manual tab
   - Name: "DVWA Demo"
   - URL: "http://dvwa.local" (or your DVWA instance)
   - Description: "Damn Vulnerable Web Application for testing"
   - Click "Add Target"

2. **Start Scan:**
   - Click "Scan" next to "DVWA Demo"
   - Watch status change to "Running"

3. **Monitor Progress:**
   - Go to Scans page
   - See real-time updates
   - Estimated time: 5-10 minutes

4. **Review Results:**
   - After completion, click on the scan
   - View discovered vulnerabilities (SQL injection, XSS, etc.)
   - Check generated patches

### Using GitHub Import

1. **Import a Repository:**
   - Go to Targets → GitHub tab
   - Enter: "https://github.com/AgentMulder404/autocTF"
   - Click "Import from GitHub"

2. **Scan GitHub Project:**
   - The target now has a GitHub icon
   - Click "Scan" to analyze the repository
   - Auto-generated PRs will appear in your GitHub repo

## Troubleshooting

### "No targets found"
- Make sure you've added at least one target using either the Manual or GitHub tab

### "Scan failed"
- Check that the target URL is accessible
- Verify environment variables are set in Vercel
- View scan logs for detailed error messages

### "API not responding"
- Refresh the page
- Check Vercel deployment status
- Ensure DATABASE_URL is correctly configured

### "GitHub PR not created"
- Verify GITHUB_TOKEN has write permissions
- Check that GITHUB_REPO is set correctly
- Ensure the repository exists and you have access

## API Documentation

For advanced users, the API is fully documented at:
```
https://autoc-82o805vdh-kevinmello8-2597s-projects.vercel.app/api/docs
```

You can also use the API directly:

```bash
# Get all targets
curl https://autoc-82o805vdh-kevinmello8-2597s-projects.vercel.app/api/targets

# Add a target from GitHub
curl -X POST https://autoc-82o805vdh-kevinmello8-2597s-projects.vercel.app/api/targets/from-github \
  -H "Content-Type: application/json" \
  -d '{"github_url": "https://github.com/username/repo"}'

# Start a scan
curl -X POST https://autoc-82o805vdh-kevinmello8-2597s-projects.vercel.app/api/targets/1/scan
```

## Next Steps

1. **Disable Vercel Auth** (Optional)
   - Go to Vercel dashboard → Settings → Deployment Protection
   - Disable "Vercel Authentication" for public access

2. **Set up Custom Domain** (Optional)
   - Go to Vercel dashboard → Settings → Domains
   - Add your custom domain (e.g., autoctf.yourdomain.com)

3. **Enable GitHub Auto-Deploy**
   - Already configured! Every push to main will auto-deploy

4. **Monitor Logs**
   - View real-time logs: `vercel logs autoc-82o805vdh-kevinmello8-2597s-projects.vercel.app --follow`

5. **Scale Up**
   - Current setup supports ~10 concurrent scans
   - For higher load, upgrade Vercel plan or adjust Neon database pool size

## Security Best Practices

1. **Never scan targets without permission**
2. **Keep API keys secure** (they're encrypted in Vercel)
3. **Review auto-generated patches** before merging
4. **Rotate credentials** regularly
5. **Monitor scan logs** for suspicious activity
6. **Use HTTPS** for all target URLs
7. **Enable authentication** in production

## Support

- GitHub Issues: https://github.com/AgentMulder404/autocTF/issues
- Documentation: See CLAUDE.md and README.md files
- API Docs: /api/docs endpoint
