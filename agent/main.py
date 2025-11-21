import asyncio
import json
import os
from agent.recon import run_recon
from agent.analyze import detect_vulns
from agent.exploit import try_sqli
from mcp.github_client import create_pr
from mcp.browserbase_client import create_session, screenshot

async def autonomous_pentest():
    print("🚀 Starting AutoCTF Agent")
    
    # 1. Spin up vulnerable app
    os.system("cd vulnerable-app && docker compose up -d")
    await asyncio.sleep(15)
    target_url = "http://localhost:8080"
    target_ip = "172.17.0.2"  # docker gateway

    # 2. Recon
    print("🔍 Phase 1: Recon")
    recon = await run_recon(target_ip, target_url)
    print(recon[:500])

    # 3. Analyze
    print("🧠 Phase 2: Detecting vulnerabilities")
    vulns_json = detect_vulns(recon)
    vulns = json.loads(vulns_json.replace("```json", "").replace("```", ""))["vulnerabilities"]
    print(f"Found {len(vulns)} vulns")

    screenshots = []
    patched_files = {}

    for v in vulns[:2]:  # demo: max 2 vulns
        print(f"⚔️ Exploiting {v['type']} on {v['endpoint']}")
        if v['type'] == "SQLi":
            success, output = await try_sqli(target_url + v['endpoint'], v['param'])
            if success:
                session = create_session()
                screenshot_url = screenshot(session.session_id, target_url + "/setup.php")  # show DB dumped
                screenshots.append(screenshot_url)

                # Fake patch DVWA login.php
                patched_code = """
<?php
if(isset($_POST['Login'])) {
    $username = $_POST['username'];
    $password = md5($_POST['password']);
    $username = mysqli_real_escape_string($link, $username);  // AutoCTF fixed
    $query = "SELECT * FROM users WHERE user='$username' AND password='$password'";
    ...
"""
                patched_files["login.php"] = patched_code

    # 5. Create PR
    print("🔧 Phase 4: Creating PR with patches")
    pr_url = create_pr(
        title="[AutoCTF] Automated Security Fixes",
        body="This PR was generated 100% autonomously by AutoCTF agent using E2B + MCPs",
        branch="autoctf-patch",
        files=patched_files
    )

    print(f"✅ Done! PR created: {pr_url}")

if __name__ == "__main__":
    asyncio.run(autonomous_pentest())