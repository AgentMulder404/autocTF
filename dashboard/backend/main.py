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
