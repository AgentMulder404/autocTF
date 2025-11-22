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
    """Analyze a GitHub repository for vulnerabilities"""

    # Extract owner and repo from URL
    match = re.search(r'github\.com/([^/]+)/([^/?]+)', github_url)
    if not match:
        return f"Invalid GitHub URL: {github_url}"

    owner, repo = match.groups()
    repo = repo.split('?')[0]  # Remove query params

    print(f"🔍 Analyzing GitHub repo: {owner}/{repo}")

    recon_output = f"""
GitHub Repository Analysis
==========================
Repository: {owner}/{repo}
URL: https://github.com/{owner}/{repo}

NOTE: This is a GitHub repository, not a live web application.
To perform actual penetration testing, you need to:
1. Clone and deploy the application locally
2. Use Docker: cd {repo} && docker-compose up -d
3. Point AutoCTF at http://localhost:PORT

Automated Code Analysis
-----------------------
"""

    try:
        # Clone and analyze the repository
        clone_cmd = f"""
        cd /tmp && \
        git clone https://github.com/{owner}/{repo}.git --depth 1 2>&1 | head -20 && \
        cd {repo} && \
        echo "Files in repository:" && \
        find . -type f -name "*.php" -o -name "*.js" -o -name "*.py" | head -20 && \
        echo "" && \
        echo "Potential config files:" && \
        find . -type f -name "config*" -o -name "*.env*" -o -name "docker-compose.yml" | head -10
        """

        result = await exec_command(clone_cmd, timeout=60)
        recon_output += result

        # Look for common vulnerabilities in code
        vuln_scan_cmd = f"""
        cd /tmp/{repo} && \
        echo "Searching for potential SQL injection patterns..." && \
        grep -r "mysql_query\\|mysqli_query" --include="*.php" | head -10 || echo "No SQL patterns found" && \
        echo "" && \
        echo "Searching for potential XSS vulnerabilities..." && \
        grep -r "echo \\$_GET\\|echo \\$_POST\\|echo \\$_REQUEST" --include="*.php" | head -10 || echo "No XSS patterns found"
        """

        vuln_result = await exec_command(vuln_scan_cmd, timeout=30)
        recon_output += "\n\nVulnerability Patterns:\n" + vuln_result

    except Exception as e:
        recon_output += f"\n\nCode analysis failed: {str(e)}"

    recon_output += f"""

NEXT STEPS FOR DVWA:
====================
To test DVWA properly:
1. Clone: git clone https://github.com/{owner}/{repo}.git
2. Start: cd {repo} && docker-compose up -d
3. Access: http://localhost:8080 (or whatever port it uses)
4. In AutoCTF: Add target with URL http://localhost:8080
5. Run scan against the live application

This GitHub repository contains INTENTIONALLY vulnerable code for training.
Deploy it locally to perform actual penetration testing.
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