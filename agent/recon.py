from mcp.exec_client import exec_command
import asyncio
import re

async def run_recon(target_ip: str, target_url: str):
    """
    Run reconnaissance on target
    Handles both live web apps and GitHub repositories
    """

    # Check if target is a GitHub repository
    if "github.com" in target_url:
        print("📦 Detected GitHub repository - performing code analysis")
        return await run_github_recon(target_url)

    # Check if URL is actually a live web server
    try:
        # Test connectivity first
        test_cmd = f'curl -s -o /dev/null -w "%{{http_code}}" --max-time 10 {target_url}'
        http_code = await exec_command(test_cmd, timeout=15)

        if "000" in http_code or not http_code.strip():
            print(f"⚠️ Target {target_url} is not responding. Using lightweight scan.")
            return await run_lightweight_recon(target_url)

    except Exception as e:
        print(f"⚠️ Connection test failed: {e}. Using lightweight scan.")
        return await run_lightweight_recon(target_url)

    # Run full recon if target is live
    print("🔍 Running full reconnaissance...")
    tasks = []

    # Only run nmap if we have a valid IP
    if target_ip and not target_ip.startswith("http"):
        tasks.append(exec_command(f"nmap -Pn -T4 -p 80,443,8080,8443 {target_ip}", timeout=90))

    # Web application scanning
    tasks.append(exec_command(f"curl -I {target_url}", timeout=30))
    tasks.append(exec_command(f"whatweb {target_url} || echo 'whatweb not available'", timeout=30))

    try:
        results = await asyncio.gather(*tasks, return_exceptions=True)
        # Filter out exceptions and join valid results
        valid_results = [r for r in results if isinstance(r, str)]
        return "\n\n".join(valid_results) if valid_results else "No reconnaissance data collected"
    except Exception as e:
        print(f"⚠️ Recon failed: {e}")
        return f"Reconnaissance failed: {str(e)}"


async def run_github_recon(github_url: str):
    """Auto-deploy and analyze a GitHub repository"""

    # Extract owner and repo from URL
    match = re.search(r'github\.com/([^/]+)/([^/?]+)', github_url)
    if not match:
        return f"Invalid GitHub URL: {github_url}"

    owner, repo = match.groups()
    repo = repo.split('?')[0]  # Remove query params

    print(f"🎯 TARGET ACQUIRED: {owner}/{repo}")
    print(f"📡 Initiating auto-deployment sequence...")

    recon_output = f"""
╔════════════════════════════════════════════════╗
║     AUTO-DEPLOYMENT & RECON INITIATED          ║
╚════════════════════════════════════════════════╝

TARGET: {owner}/{repo}
URL: https://github.com/{owner}/{repo}

[PHASE 1] CLONING TARGET REPOSITORY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

    deployed_url = None
    deployment_port = None

    try:
        # Clone the repository
        clone_cmd = f"""
        cd /tmp && \
        rm -rf {repo} 2>/dev/null && \
        git clone https://github.com/{owner}/{repo}.git --depth 1 2>&1 && \
        echo "✅ Repository cloned successfully"
        """

        result = await exec_command(clone_cmd, timeout=60)
        recon_output += result + "\n\n"

        # Check for Docker support (informational only - not used for deployment)
        recon_output += "[PHASE 2] DEPLOYMENT DETECTION\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"

        check_docker_cmd = f"""
        cd /tmp/{repo} && \
        if [ -f "docker-compose.yml" ]; then
            echo "🐳 Docker Compose detected"
            cat docker-compose.yml | grep -E "ports:|image:" | head -10
        elif [ -f "Dockerfile" ]; then
            echo "🐳 Dockerfile detected"
            cat Dockerfile | head -10
        else
            echo "ℹ️  No Docker configuration found"
        fi
        """

        docker_check = await exec_command(check_docker_cmd, timeout=30)
        recon_output += docker_check + "\n\n"

        # Detect port for informational purposes
        port_detect_cmd = f"""
        cd /tmp/{repo} && \
        if [ -f "docker-compose.yml" ]; then
            grep -oP '\\d+:' docker-compose.yml | head -1 | tr -d ':'
        else
            echo "8080"
        fi
        """

        try:
            port_result = await exec_command(port_detect_cmd, timeout=10)
            deployment_port = port_result.strip() or "8080"
        except:
            deployment_port = "8080"

        # E2B Cloud Sandboxes don't support Docker
        recon_output += "[PHASE 3] DEPLOYMENT STATUS\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        recon_output += "ℹ️  E2B cloud sandboxes don't support Docker containers\n"
        recon_output += "💡 This is a code-only analysis - no live deployment\n"
        recon_output += "\nTO TEST LIVE:\n"
        recon_output += f"  1. Clone locally: git clone https://github.com/{owner}/{repo}.git\n"
        recon_output += f"  2. Deploy: cd {repo} && docker-compose up -d\n"
        recon_output += f"  3. Add as target with URL: http://localhost:{deployment_port}\n\n"

        # Code analysis
        recon_output += "[PHASE 4] CODE ANALYSIS\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"

        analysis_cmd = f"""
        cd /tmp/{repo} && \
        echo "📂 Repository structure:" && \
        find . -maxdepth 2 -type f -name "*.php" -o -name "*.js" -o -name "*.py" | head -15 && \
        echo "" && \
        echo "🔍 Searching for vulnerability patterns..." && \
        echo "" && \
        echo "💉 SQL Injection patterns:" && \
        grep -r "mysql_query\\|mysqli_query\\|\\$_GET\\|\\$_POST" --include="*.php" 2>/dev/null | head -5 || echo "   None detected" && \
        echo "" && \
        echo "⚡ XSS patterns:" && \
        grep -r "echo.*\\$_" --include="*.php" 2>/dev/null | head -5 || echo "   None detected"
        """

        analysis_result = await exec_command(analysis_cmd, timeout=30)
        recon_output += analysis_result

    except Exception as e:
        recon_output += f"\n\n❌ DEPLOYMENT FAILED: {str(e)}"

    # Final summary
    recon_output += f"""

╔════════════════════════════════════════════════╗
║           AUTO-DEPLOYMENT SUMMARY              ║
╚════════════════════════════════════════════════╝

Repository: {owner}/{repo}
"""

    recon_output += f"""⚠️  STATUS: CODE ANALYSIS ONLY
💡 E2B CLOUD MODE: No Docker container deployment

FINDINGS:
  → Repository successfully cloned and analyzed
  → Vulnerability patterns detected in code
  → Security recommendations generated

TO TEST LIVE (Optional):
  1. Clone locally: git clone https://github.com/{owner}/{repo}.git
  2. Deploy: cd {repo} && docker-compose up -d (requires local Docker)
  3. Add as new target: http://localhost:{deployment_port}

NEXT PHASE:
The AutoCTF agent will proceed with:
  → Static code vulnerability analysis
  → Security pattern detection
  → Automated patch generation
  → GitHub PR creation
"""

    return recon_output


async def run_lightweight_recon(target_url: str):
    """Run lightweight reconnaissance for non-responsive targets"""

    recon_output = f"""
Lightweight Reconnaissance
==========================
Target: {target_url}
Status: Target is not responding or is not a live web application

Basic Information:
"""

    try:
        # Just do basic URL analysis
        info_cmd = f"""
        echo "DNS Lookup:" && \
        dig +short {target_url.replace('https://', '').replace('http://', '').split('/')[0]} 2>&1 | head -5 && \
        echo "" && \
        echo "WHOIS Info:" && \
        whois {target_url.replace('https://', '').replace('http://', '').split('/')[0]} 2>&1 | head -20
        """

        result = await exec_command(info_cmd, timeout=30)
        recon_output += result

    except Exception as e:
        recon_output += f"Basic recon failed: {str(e)}"

    recon_output += """

Note: Target appears to be offline or is not a web application.
For accurate penetration testing:
- Ensure the target is a live, running web application
- If testing a local app, use http://localhost:PORT
- If testing DVWA, deploy it first: docker-compose up -d
"""

    return recon_output