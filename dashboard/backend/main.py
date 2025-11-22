from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
import asyncio
from datetime import datetime, timedelta

from database import get_db, init_db
from models import Target, PentestRun, Vulnerability, Patch
from schemas import (
    TargetCreate, TargetUpdate, TargetResponse, TargetFromGitHub,
    RunCreate, RunResponse, RunDetailResponse,
    VulnerabilityResponse, VulnerabilityUpdate,
    PatchResponse, OverviewStats, TrendData
)
from pentest_worker import PentestWorker
from github_utils import extract_target_info_from_github

# Initialize FastAPI
app = FastAPI(
    title="AutoCTF Enterprise Dashboard",
    description="Autonomous penetration testing and patching platform",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize DB on startup
@app.on_event("startup")
def startup():
    init_db()
    print("🚀 AutoCTF Dashboard API started")

# Health check
@app.get("/")
def root():
    return {"message": "AutoCTF Dashboard API", "status": "running"}

# ============================================
# TARGET ENDPOINTS
# ============================================

@app.get("/api/targets", response_model=List[TargetResponse])
def list_targets(db: Session = Depends(get_db)):
    """List all targets"""
    targets = db.query(Target).all()

    # Add active scan status to each target
    results = []
    for target in targets:
        target_dict = {
            "id": target.id,
            "name": target.name,
            "url": target.url,
            "ip_address": target.ip_address,
            "github_repo": target.github_repo,
            "github_branch": target.github_branch,
            "repo_owner": target.repo_owner,
            "repo_name": target.repo_name,
            "status": target.status,
            "created_at": target.created_at,
            "last_scan": target.last_scan,
            "has_active_scan": any(run.status in ["queued", "running"] for run in target.runs)
        }
        results.append(target_dict)

    return results

@app.post("/api/targets", response_model=TargetResponse)
def create_target(target: TargetCreate, db: Session = Depends(get_db)):
    """Create a new target"""
    db_target = Target(**target.dict())
    db.add(db_target)
    db.commit()
    db.refresh(db_target)
    return db_target

@app.post("/api/targets/from-github", response_model=TargetResponse)
def create_target_from_github(github_data: TargetFromGitHub, db: Session = Depends(get_db)):
    """Create a target from a GitHub repository URL"""
    try:
        # Extract target info from GitHub URL
        target_info = extract_target_info_from_github(github_data.github_url)

        # Create target with extracted info
        db_target = Target(**target_info)
        db.add(db_target)
        db.commit()
        db.refresh(db_target)
        return db_target
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process GitHub URL: {str(e)}")

@app.get("/api/targets/{target_id}", response_model=TargetResponse)
def get_target(target_id: int, db: Session = Depends(get_db)):
    """Get target by ID"""
    target = db.query(Target).filter(Target.id == target_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")
    return target

@app.put("/api/targets/{target_id}", response_model=TargetResponse)
def update_target(target_id: int, target_update: TargetUpdate, db: Session = Depends(get_db)):
    """Update target"""
    target = db.query(Target).filter(Target.id == target_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")

    for key, value in target_update.dict(exclude_unset=True).items():
        setattr(target, key, value)

    db.commit()
    db.refresh(target)
    return target

@app.delete("/api/targets/{target_id}")
def delete_target(target_id: int, db: Session = Depends(get_db)):
    """Delete target"""
    target = db.query(Target).filter(Target.id == target_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")

    db.delete(target)
    db.commit()
    return {"message": "Target deleted"}

# ============================================
# PENTEST RUN ENDPOINTS
# ============================================

@app.post("/api/targets/{target_id}/scan", response_model=RunResponse)
async def start_scan(target_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Start a pentest scan for target"""
    target = db.query(Target).filter(Target.id == target_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")

    # Create run
    run = PentestRun(target_id=target_id, status="queued")
    db.add(run)
    db.commit()
    db.refresh(run)

    # Start pentest in background
    background_tasks.add_task(run_pentest_task, run.id)

    return run

def run_pentest_task(run_id: int):
    """Background task wrapper for pentest"""
    from database import SessionLocal
    db = SessionLocal()
    try:
        asyncio.run(PentestWorker.run_pentest(run_id, db))
    finally:
        db.close()

@app.get("/api/runs", response_model=List[RunResponse])
def list_runs(db: Session = Depends(get_db)):
    """List all pentest runs"""
    runs = db.query(PentestRun).order_by(PentestRun.started_at.desc()).all()
    return runs

@app.get("/api/runs/{run_id}", response_model=RunDetailResponse)
def get_run(run_id: int, db: Session = Depends(get_db)):
    """Get pentest run details"""
    run = db.query(PentestRun).filter(PentestRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run

@app.get("/api/runs/{run_id}/status")
def get_run_status(run_id: int, db: Session = Depends(get_db)):
    """Get real-time status of a run"""
    run = db.query(PentestRun).filter(PentestRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    return {
        "id": run.id,
        "status": run.status,
        "started_at": run.started_at,
        "completed_at": run.completed_at,
        "vuln_count": len(run.vulnerabilities)
    }

@app.delete("/api/runs/{run_id}")
def delete_run(run_id: int, db: Session = Depends(get_db)):
    """Delete a pentest run (or cancel if running)"""
    run = db.query(PentestRun).filter(PentestRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    if run.status in ["queued", "running"]:
        # Cancel running scans instead of deleting
        run.status = "cancelled"
        run.completed_at = datetime.utcnow()
        db.commit()
        return {"message": "Run cancelled"}
    else:
        # Delete completed/failed/cancelled runs
        db.delete(run)
        db.commit()
        return {"message": "Run deleted"}

@app.get("/api/runs/{run_id}/summary")
def get_run_summary(run_id: int, db: Session = Depends(get_db)):
    """Generate a written summary report for a pentest run"""
    run = db.query(PentestRun).filter(PentestRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    target = run.target
    vulns = run.vulnerabilities

    # Calculate statistics
    total_vulns = len(vulns)
    critical_vulns = len([v for v in vulns if v.severity == "critical"])
    high_vulns = len([v for v in vulns if v.severity == "high"])
    medium_vulns = len([v for v in vulns if v.severity == "medium"])
    low_vulns = len([v for v in vulns if v.severity == "low"])

    # Calculate duration
    duration = "N/A"
    if run.started_at and run.completed_at:
        delta = run.completed_at - run.started_at
        hours, remainder = divmod(int(delta.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        if hours > 0:
            duration = f"{hours}h {minutes}m"
        else:
            duration = f"{minutes}m {seconds}s"

    # Generate summary text with hackerish tone
    summary = f"""# [PENTEST REPORT] {target.name} - Security Assessment

```
╔═══════════════════════════════════════════════════════════════╗
║                    TARGET ACQUIRED                             ║
║                  AUTONOMOUS PENTEST REPORT                     ║
╚═══════════════════════════════════════════════════════════════╝
```

## 📡 TARGET INTEL
- **Designation:** {target.name}
- **Attack Surface:** {target.url}
- **Engagement Time:** {run.started_at.strftime("%B %d, %Y at %I:%M %p") if run.started_at else "N/A"}
- **Op Duration:** {duration}
- **Mission Status:** {run.status.upper()}

## 🎯 ENGAGEMENT SUMMARY
Ran a full-spectrum autonomous pentest on the target using AutoCTF's AI-powered exploitation framework. This wasn't your typical scan-and-report job - we went deep with active recon, vulnerability enumeration, and live exploitation attempts to see what could actually be pwned.

## 💀 DAMAGE REPORT
- **Total Vulns Discovered:** {total_vulns}
  - CRITICAL (own the box): {critical_vulns}
  - HIGH (serious breach): {high_vulns}
  - MEDIUM (attack vector): {medium_vulns}
  - LOW (info leak): {low_vulns}

## 🔥 THREAT LEVEL ASSESSMENT
"""

    if critical_vulns > 0:
        summary += f"\n🚨 **CODE RED** - {critical_vulns} CRITICAL vulns detected. Target is HIGHLY EXPLOITABLE. This box can be OWNED. Patch ASAP or prepare for breach.\n"
    elif high_vulns > 0:
        summary += f"\n⚠️ **DEFCON 2** - Found {high_vulns} HIGH severity vulns. Target has serious attack vectors. An attacker could do significant damage. Fix immediately.\n"
    elif medium_vulns > 0:
        summary += f"\n⚡ **ELEVATED RISK** - Discovered {medium_vulns} MEDIUM severity issues. Not immediately critical but these create opportunities for lateral movement. Don't sleep on these.\n"
    elif low_vulns > 0:
        summary += f"\n✓ **MINOR EXPOSURE** - Only {low_vulns} LOW severity issues found. Target is relatively hardened but still has some info leakage. Clean these up when you can.\n"
    else:
        summary += "\n✅ **FORTRESS MODE** - No exploitable vulns found in this run. Either the target is well-secured or we need deeper enumeration. Nice work on the security posture.\n"

    summary += "\n## 🔍 DETAILED EXPLOITATION FINDINGS\n"

    if total_vulns > 0:
        # Group vulnerabilities by severity
        severity_emojis = {"critical": "💀", "high": "🔴", "medium": "🟠", "low": "🟡"}
        for severity in ["critical", "high", "medium", "low"]:
            severity_vulns = [v for v in vulns if v.severity == severity]
            if severity_vulns:
                emoji = severity_emojis.get(severity, "⚠️")
                summary += f"\n### {emoji} {severity.upper()} SEVERITY - {len(severity_vulns)} DISCOVERED\n"
                for vuln in severity_vulns:
                    summary += f"\n#### [{vuln.vuln_type}] {vuln.title}\n"
                    summary += f"- **Attack Vector:** {vuln.description}\n"
                    if vuln.proof:
                        summary += f"- **Exploitation Status:** ✓ CONFIRMED - Proof of concept executed successfully\n"
                    if vuln.cvss_score:
                        summary += f"- **CVSS Score:** {vuln.cvss_score}\n"
                    summary += "\n"
    else:
        summary += "\nNo exploitable vulnerabilities were discovered in this engagement. Target appears hardened against automated exploitation techniques.\n"

    summary += """
## 🛡️ REMEDIATION PROTOCOL

"""

    if total_vulns > 0:
        summary += """### IMMEDIATE ACTIONS (DO THIS NOW):
   1. 🚨 **Triage Critical/High vulns** - These are your active threats. Drop everything and patch these first
   2. 🔧 **Deploy Auto-Patches** - Check the GitHub PRs generated by AutoCTF. Review and merge ASAP
   3. 🛡️ **Implement Input Validation** - Most of these vulns come from trusting user input. Never trust user input
   4. 🔒 **Enable Security Headers** - CSP, HSTS, X-Frame-Options - the usual suspects

### SHORT-TERM TACTICS:
   - Review all flagged endpoints and sanitize inputs
   - Update dependencies (check for known CVEs)
   - Run another scan after patching to verify fixes
   - Enable logging for the affected components to detect active exploitation

### LONG-TERM STRATEGY:
   - Integrate AutoCTF into your CI/CD pipeline for continuous testing
   - Implement a bug bounty program (find vulns before bad actors do)
   - Run red team exercises quarterly
   - Train your devs on secure coding practices (OWASP Top 10 minimum)

"""
    else:
        summary += """### MAINTAIN THE FORTRESS:
   - Keep running regular pentests (quarterly minimum)
   - Stay current with patches and updates
   - Monitor security advisories for your stack
   - Implement defense-in-depth (WAF, IDS/IPS, honeypots)
   - Don't get complacent - attackers are always evolving

"""

    summary += f"""## 🔬 ATTACK METHODOLOGY

This engagement followed a structured kill chain:
1. **RECON** - Enumerated the attack surface (nmap, service discovery, endpoint mapping)
2. **SCANNING** - Ran automated vuln scanners (nikto, gobuster, custom fuzzing)
3. **EXPLOITATION** - Actively exploited discovered vulns (SQLi, XSS, auth bypass, etc.)
4. **VALIDATION** - Captured proof-of-concept evidence (screenshots, payloads, data exfil)
5. **PATCHING** - Auto-generated security patches using AI (check your PRs)

## 📋 ACTION ITEMS

1. ⚡ Review this report with your security/dev team
2. 🎯 Prioritize remediation by severity (Critical -> High -> Medium -> Low)
3. 💾 Check GitHub repo for auto-generated patches
4. 🔄 Re-run AutoCTF after patching to verify fixes
5. 📊 Track metrics - measure your security posture improvement over time

## 📡 ENGAGEMENT METADATA
```
Report Generated: {datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")}
Autonomous Agent: AutoCTF v1.0
Run ID: #{run.id}
Operator: AI Pentest Engine
Status: MISSION COMPLETE
```

---
```
[END REPORT]

This assessment was fully automated by AutoCTF's AI-powered pentesting engine.
For detailed technical analysis, review the full scan output in the dashboard.

Stay secure. Stay paranoid. 🔒
```
"""

    return {
        "run_id": run.id,
        "target_name": target.name,
        "summary": summary,
        "statistics": {
            "total_vulnerabilities": total_vulns,
            "critical": critical_vulns,
            "high": high_vulns,
            "medium": medium_vulns,
            "low": low_vulns,
            "duration": duration,
            "status": run.status
        }
    }

# ============================================
# VULNERABILITY ENDPOINTS
# ============================================

@app.get("/api/vulnerabilities", response_model=List[VulnerabilityResponse])
def list_vulnerabilities(db: Session = Depends(get_db)):
    """List all vulnerabilities"""
    vulns = db.query(Vulnerability).order_by(Vulnerability.created_at.desc()).all()
    return vulns

@app.get("/api/vulnerabilities/{vuln_id}", response_model=VulnerabilityResponse)
def get_vulnerability(vuln_id: int, db: Session = Depends(get_db)):
    """Get vulnerability details"""
    vuln = db.query(Vulnerability).filter(Vulnerability.id == vuln_id).first()
    if not vuln:
        raise HTTPException(status_code=404, detail="Vulnerability not found")
    return vuln

@app.put("/api/vulnerabilities/{vuln_id}", response_model=VulnerabilityResponse)
def update_vulnerability(vuln_id: int, vuln_update: VulnerabilityUpdate, db: Session = Depends(get_db)):
    """Update vulnerability"""
    vuln = db.query(Vulnerability).filter(Vulnerability.id == vuln_id).first()
    if not vuln:
        raise HTTPException(status_code=404, detail="Vulnerability not found")

    for key, value in vuln_update.dict(exclude_unset=True).items():
        setattr(vuln, key, value)

    db.commit()
    db.refresh(vuln)
    return vuln

# ============================================
# ANALYTICS ENDPOINTS
# ============================================

@app.get("/api/analytics/overview", response_model=OverviewStats)
def get_overview(db: Session = Depends(get_db)):
    """Get dashboard overview statistics"""
    total_targets = db.query(Target).count()
    active_scans = db.query(PentestRun).filter(PentestRun.status == "running").count()
    total_vulns = db.query(Vulnerability).count()
    critical_vulns = db.query(Vulnerability).filter(Vulnerability.severity == "critical").count()
    high_vulns = db.query(Vulnerability).filter(Vulnerability.severity == "high").count()
    patched_vulns = db.query(Vulnerability).filter(Vulnerability.patched == True).count()
    open_prs = db.query(Patch).filter(Patch.status == "created").count()

    return OverviewStats(
        total_targets=total_targets,
        active_scans=active_scans,
        total_vulnerabilities=total_vulns,
        critical_vulns=critical_vulns,
        high_vulns=high_vulns,
        patched_vulns=patched_vulns,
        open_prs=open_prs
    )

@app.get("/api/analytics/trends", response_model=List[TrendData])
def get_trends(days: int = 30, db: Session = Depends(get_db)):
    """Get vulnerability trends over time"""
    # Simplified - returns last N days
    trends = []
    for i in range(days):
        date = datetime.utcnow() - timedelta(days=i)
        date_str = date.strftime("%Y-%m-%d")

        vulns = db.query(Vulnerability).filter(
            Vulnerability.created_at >= date,
            Vulnerability.created_at < date + timedelta(days=1)
        ).count()

        patched = db.query(Vulnerability).filter(
            Vulnerability.created_at >= date,
            Vulnerability.created_at < date + timedelta(days=1),
            Vulnerability.patched == True
        ).count()

        trends.append(TrendData(date=date_str, vulnerabilities=vulns, patched=patched))

    return trends[::-1]  # Reverse to chronological order

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
