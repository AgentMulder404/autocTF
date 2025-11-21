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
    return targets

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
def cancel_run(run_id: int, db: Session = Depends(get_db)):
    """Cancel a running pentest"""
    run = db.query(PentestRun).filter(PentestRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    if run.status in ["queued", "running"]:
        run.status = "cancelled"
        run.completed_at = datetime.utcnow()
        db.commit()

    return {"message": "Run cancelled"}

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

    # Generate summary text
    summary = f"""# Penetration Test Summary Report

## Target Information
- **Name:** {target.name}
- **URL:** {target.url}
- **Test Date:** {run.started_at.strftime("%B %d, %Y at %I:%M %p") if run.started_at else "N/A"}
- **Duration:** {duration}
- **Status:** {run.status.upper()}

## Executive Summary
This automated penetration test was conducted on {target.name} using AutoCTF's autonomous testing framework. The assessment included reconnaissance, vulnerability scanning, and exploitation attempts to identify security weaknesses.

## Key Findings
- **Total Vulnerabilities Found:** {total_vulns}
  - Critical: {critical_vulns}
  - High: {high_vulns}
  - Medium: {medium_vulns}
  - Low: {low_vulns}

## Risk Assessment
"""

    if critical_vulns > 0:
        summary += f"\n⚠️ **CRITICAL RISK**: {critical_vulns} critical vulnerabilities detected. Immediate action required.\n"
    elif high_vulns > 0:
        summary += f"\n⚡ **HIGH RISK**: {high_vulns} high-severity vulnerabilities found. Prioritize remediation.\n"
    elif medium_vulns > 0:
        summary += f"\n⚠️ **MEDIUM RISK**: {medium_vulns} medium-severity issues identified. Address in next update cycle.\n"
    elif low_vulns > 0:
        summary += f"\n✓ **LOW RISK**: Only {low_vulns} low-severity issues found. Good security posture.\n"
    else:
        summary += "\n✅ **SECURE**: No vulnerabilities detected in this assessment.\n"

    summary += "\n## Detailed Findings\n"

    if total_vulns > 0:
        # Group vulnerabilities by severity
        for severity in ["critical", "high", "medium", "low"]:
            severity_vulns = [v for v in vulns if v.severity == severity]
            if severity_vulns:
                summary += f"\n### {severity.upper()} Severity ({len(severity_vulns)})\n"
                for vuln in severity_vulns:
                    summary += f"\n#### {vuln.title}\n"
                    summary += f"- **Type:** {vuln.vuln_type}\n"
                    summary += f"- **Description:** {vuln.description}\n"
                    if vuln.proof:
                        summary += f"- **Proof of Exploitation:** Found\n"
                    if vuln.cvss_score:
                        summary += f"- **CVSS Score:** {vuln.cvss_score}\n"
                    summary += "\n"
    else:
        summary += "\nNo vulnerabilities were identified during this assessment.\n"

    summary += """
## Recommendations

"""

    if total_vulns > 0:
        summary += """1. **Immediate Actions:**
   - Review and validate all critical and high-severity findings
   - Apply security patches for identified vulnerabilities
   - Implement input validation and sanitization

2. **Short-term Actions:**
   - Deploy auto-generated patches (check GitHub PRs)
   - Update security policies and configurations
   - Conduct code review for affected components

3. **Long-term Actions:**
   - Implement continuous security testing in CI/CD pipeline
   - Conduct security training for development team
   - Establish regular penetration testing schedule

"""
    else:
        summary += """1. **Maintain Security Posture:**
   - Continue regular security assessments
   - Keep all dependencies and frameworks updated
   - Monitor for new vulnerabilities in third-party components

2. **Proactive Measures:**
   - Implement additional security layers (WAF, IDS/IPS)
   - Conduct regular security audits
   - Stay informed about emerging threats

"""

    summary += f"""## Testing Methodology

This assessment utilized the following approach:
1. **Reconnaissance:** Network scanning and service enumeration
2. **Vulnerability Scanning:** Automated security testing with industry-standard tools
3. **Exploitation:** Attempted exploitation of discovered vulnerabilities
4. **Validation:** Proof-of-concept demonstrations
5. **Reporting:** Automated patch generation and documentation

## Next Steps

- Review this report with your security team
- Prioritize remediation based on severity levels
- Check GitHub repository for auto-generated security patches
- Schedule follow-up testing after remediation

## Report Generated
- **Date:** {datetime.utcnow().strftime("%B %d, %Y at %I:%M %p UTC")}
- **By:** AutoCTF Autonomous Pentesting Platform
- **Run ID:** {run.id}

---
*This report was automatically generated by AutoCTF. For questions or detailed analysis, review the full scan results in the dashboard.*
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
