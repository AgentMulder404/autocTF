"""
AutoCTF Production Backend - Railway Deployment
Refactored for:
- Railway long-running API server
- Trigger.dev background job queue
- Server-Sent Events (SSE) for real-time updates
- Vercel frontend CORS support
"""

from fastapi import FastAPI, Depends, HTTPException, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import asyncio
import json
from datetime import datetime
from dotenv import load_dotenv
import os
import sys
import httpx
from collections import defaultdict

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '../../.env'))

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from database import get_db, init_db
from models import Target, PentestRun, Vulnerability, Patch
from schemas import (
    TargetCreate, TargetUpdate, TargetResponse, TargetFromGitHub,
    RunCreate, RunResponse, RunDetailResponse,
    VulnerabilityResponse, VulnerabilityUpdate,
    PatchResponse, OverviewStats, TrendData
)
from github_utils import extract_target_info_from_github, GitHubURLError

# Import pentest modules for internal endpoints
from agent.recon import run_recon
from agent.analyze import detect_vulns
from agent.exploit import try_sqli

# Configure logging
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="AutoCTF Enterprise API",
    description="Production-ready pentest automation with Railway + Trigger.dev",
    version="2.0.0"
)

# Production CORS - Allow Vercel frontend
ALLOWED_ORIGINS = [
    "http://localhost:3000",  # Local development
    "http://localhost:5173",  # Vite dev server
    os.getenv("FRONTEND_URL", ""),  # Vercel production URL
    "*",  # Remove in production, use specific origins
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# SSE event streams storage (in-memory for now, use Redis in production)
sse_subscribers = defaultdict(list)

# Configuration
TRIGGER_API_KEY = os.getenv("TRIGGER_API_KEY", "")
TRIGGER_API_URL = os.getenv("TRIGGER_API_URL", "https://api.trigger.dev")
BACKEND_API_KEY = os.getenv("BACKEND_API_KEY", "your-secret-api-key-here")
BACKEND_URL = os.getenv("RAILWAY_PUBLIC_URL", "http://localhost:8000")

# ============================================
# STARTUP & HEALTH
# ============================================

@app.on_event("startup")
async def startup():
    """Initialize database and services"""
    logger.info("🚀 AutoCTF Production API starting...")
    logger.info("=" * 60)

    try:
        init_db()
        logger.info("✅ Database initialized")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        raise

    logger.info(f"✅ CORS configured for: {ALLOWED_ORIGINS}")
    logger.info(f"✅ Trigger.dev: {TRIGGER_API_URL}")
    logger.info(f"✅ Backend URL: {BACKEND_URL}")
    logger.info("=" * 60)


@app.get("/")
def root():
    """API root"""
    return {
        "message": "AutoCTF Production API",
        "version": "2.0.0",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health")
def health_check():
    """Railway health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.0.0",
        "services": {
            "database": "connected",
            "trigger_dev": "configured" if TRIGGER_API_KEY else "not_configured"
        }
    }


# ============================================
# SSE (Server-Sent Events) for Real-time Updates
# ============================================

@app.get("/api/runs/{run_id}/stream")
async def stream_run_updates(run_id: int):
    """
    Server-Sent Events endpoint for real-time scan progress

    Usage from frontend:
    const eventSource = new EventSource(`/api/runs/${runId}/stream`);
    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);
      console.log("Progress:", data.message);
    };
    """
    async def event_generator():
        try:
            # Send initial connection message
            yield f"data: {json.dumps({'status': 'connected', 'runId': run_id})}\n\n"

            # Keep connection alive and send updates
            while True:
                # Check if there are any updates for this run_id
                if run_id in sse_subscribers:
                    for update in sse_subscribers[run_id]:
                        yield f"data: {json.dumps(update)}\n\n"
                    sse_subscribers[run_id].clear()

                # Send heartbeat every 30 seconds
                yield f": heartbeat\n\n"
                await asyncio.sleep(5)

        except asyncio.CancelledError:
            logger.info(f"SSE connection closed for run {run_id}")

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        }
    )


async def broadcast_progress(run_id: int, status: str, message: str):
    """Broadcast progress update to SSE subscribers"""
    update = {
        "runId": run_id,
        "status": status,
        "message": message,
        "timestamp": datetime.utcnow().isoformat()
    }
    sse_subscribers[run_id].append(update)
    logger.info(f"[SSE] Broadcast to run {run_id}: {message}")


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
def create_target_from_github(github_target: TargetFromGitHub, db: Session = Depends(get_db)):
    """Import target from GitHub repository"""
    try:
        target_info = extract_target_info_from_github(github_target.github_url)

        # Check if target already exists
        existing = db.query(Target).filter(
            Target.github_repo == target_info["github_repo"]
        ).first()

        if existing:
            raise HTTPException(
                status_code=409,
                detail=f"Target '{target_info['name']}' already exists. Delete the existing target first or use a different repository."
            )

        # Create new target
        db_target = Target(**target_info)
        db.add(db_target)
        db.commit()
        db.refresh(db_target)

        logger.info(f"✅ Created target from GitHub: {target_info['name']}")
        return db_target

    except GitHubURLError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"GitHub import error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to import from GitHub: {str(e)}")


@app.get("/api/targets/{target_id}", response_model=TargetResponse)
def get_target(target_id: int, db: Session = Depends(get_db)):
    """Get target by ID"""
    target = db.query(Target).filter(Target.id == target_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")
    return target


@app.delete("/api/targets/{target_id}")
def delete_target(target_id: int, db: Session = Depends(get_db)):
    """Delete a target"""
    target = db.query(Target).filter(Target.id == target_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")

    db.delete(target)
    db.commit()
    return {"message": "Target deleted successfully"}


# ============================================
# PENTEST RUN ENDPOINTS (Trigger.dev Integration)
# ============================================

@app.post("/api/targets/{target_id}/scan", response_model=RunResponse)
async def start_scan(target_id: int, db: Session = Depends(get_db)):
    """
    Start pentest scan via Trigger.dev

    Instead of running pentest in BackgroundTasks (which doesn't work on Vercel),
    we queue it to Trigger.dev which handles long-running jobs.
    """
    target = db.query(Target).filter(Target.id == target_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")

    # Create pending run
    run = PentestRun(target_id=target_id, status="queued")
    db.add(run)
    db.commit()
    db.refresh(run)

    logger.info(f"🚀 Queueing pentest scan for target {target_id}, run {run.id}")

    # Queue job to Trigger.dev
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{TRIGGER_API_URL}/api/v1/events",
                headers={
                    "Authorization": f"Bearer {TRIGGER_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "id": f"pentest-{run.id}",
                    "event": "pentest.scan.start",
                    "payload": {
                        "runId": run.id,
                        "targetId": target.id,
                        "targetUrl": target.url,
                        "targetIp": target.ip_address,
                        "githubRepo": target.github_repo,
                        "backendUrl": BACKEND_URL,
                        "backendApiKey": BACKEND_API_KEY
                    }
                },
                timeout=30.0
            )

            if response.status_code not in [200, 201]:
                logger.error(f"Trigger.dev error: {response.text}")
                run.status = "failed"
                run.error_message = f"Failed to queue job: {response.text}"
                db.commit()
                raise HTTPException(status_code=500, detail="Failed to queue scan job")

            logger.info(f"✅ Scan queued to Trigger.dev: run {run.id}")

    except httpx.RequestError as e:
        logger.error(f"Failed to reach Trigger.dev: {e}")
        run.status = "failed"
        run.error_message = f"Job queue unavailable: {str(e)}"
        db.commit()
        raise HTTPException(status_code=503, detail="Job queue service unavailable")

    return run


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


# ============================================
# INTERNAL ENDPOINTS (Called by Trigger.dev)
# ============================================

def verify_internal_api_key(x_api_key: Optional[str] = Header(None)):
    """Verify internal API key for Trigger.dev callbacks"""
    if not x_api_key or x_api_key != BACKEND_API_KEY:
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API key"
        )
    return x_api_key


@app.post("/internal/run-recon")
async def internal_run_recon(
    request: dict,
    api_key: str = Depends(verify_internal_api_key),
    db: Session = Depends(get_db)
):
    """
    Internal endpoint called by Trigger.dev to run reconnaissance
    """
    run_id = request.get("runId")
    target_url = request.get("targetUrl")
    target_ip = request.get("targetIp")

    logger.info(f"[Internal] Running recon for run {run_id}")

    try:
        # Run recon using E2B sandbox
        recon_output = await run_recon(target_ip or target_url, target_url)

        # Update run in database
        run = db.query(PentestRun).filter(PentestRun.id == run_id).first()
        if run:
            run.recon_output = recon_output
            run.status = "running"
            db.commit()

        # Broadcast progress via SSE
        await broadcast_progress(run_id, "running", "Reconnaissance complete")

        return {"output": recon_output}

    except Exception as e:
        logger.error(f"[Internal] Recon failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/internal/analyze-vulns")
async def internal_analyze_vulns(
    request: dict,
    api_key: str = Depends(verify_internal_api_key),
    db: Session = Depends(get_db)
):
    """
    Internal endpoint called by Trigger.dev to analyze vulnerabilities
    """
    run_id = request.get("runId")
    recon_output = request.get("reconOutput")

    logger.info(f"[Internal] Analyzing vulnerabilities for run {run_id}")

    try:
        # Detect vulnerabilities using xAI Grok
        vulns_json = detect_vulns(recon_output)

        # Parse JSON
        vulns_data = json.loads(vulns_json.replace("```json", "").replace("```", ""))
        vulnerabilities = vulns_data.get("vulnerabilities", [])

        # Update run in database
        run = db.query(PentestRun).filter(PentestRun.id == run_id).first()
        if run:
            run.vulnerabilities_json = vulns_data
            db.commit()

            # Create Vulnerability records
            for vuln in vulnerabilities:
                db_vuln = Vulnerability(
                    run_id=run_id,
                    type=vuln.get("type", "unknown"),
                    severity=vuln.get("severity", "medium"),
                    endpoint=vuln.get("endpoint", ""),
                    description=vuln.get("description", ""),
                    proof=vuln.get("proof", "")
                )
                db.add(db_vuln)
            db.commit()

        # Broadcast progress
        await broadcast_progress(
            run_id,
            "running",
            f"Found {len(vulnerabilities)} vulnerabilities"
        )

        return {"vulnerabilities": vulnerabilities}

    except Exception as e:
        logger.error(f"[Internal] Analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/internal/exploit-vulns")
async def internal_exploit_vulns(
    request: dict,
    api_key: str = Depends(verify_internal_api_key)
):
    """
    Internal endpoint called by Trigger.dev to exploit vulnerabilities
    """
    run_id = request.get("runId")
    target_url = request.get("targetUrl")
    vulnerabilities = request.get("vulnerabilities", [])

    logger.info(f"[Internal] Exploiting {len(vulnerabilities)} vulns for run {run_id}")

    results = []

    try:
        for vuln in vulnerabilities:
            if vuln.get("type") == "SQL Injection":
                endpoint = vuln.get("endpoint", "")
                param = vuln.get("param", "id")

                # Try SQL injection
                success, dump_data = await try_sqli(f"{target_url}{endpoint}", param)

                results.append({
                    "type": "SQL Injection",
                    "endpoint": endpoint,
                    "success": success,
                    "data": dump_data
                })

        # Broadcast progress
        await broadcast_progress(run_id, "running", "Exploitation complete")

        return {"results": results}

    except Exception as e:
        logger.error(f"[Internal] Exploitation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/internal/scan-progress")
async def internal_scan_progress(
    request: dict,
    api_key: str = Depends(verify_internal_api_key),
    db: Session = Depends(get_db)
):
    """
    Receive progress updates from Trigger.dev and broadcast via SSE
    """
    run_id = request.get("runId")
    status = request.get("status")
    message = request.get("message")

    logger.info(f"[Progress] Run {run_id}: {status} - {message}")

    # Update database
    run = db.query(PentestRun).filter(PentestRun.id == run_id).first()
    if run:
        run.status = status
        if status == "failed":
            run.error_message = message
            run.completed_at = datetime.utcnow()
        elif status == "completed":
            run.completed_at = datetime.utcnow()
        db.commit()

    # Broadcast to SSE clients
    await broadcast_progress(run_id, status, message)

    return {"status": "ok"}


# ============================================
# VULNERABILITY ENDPOINTS
# ============================================

@app.get("/api/vulnerabilities", response_model=List[VulnerabilityResponse])
def list_vulnerabilities(db: Session = Depends(get_db)):
    """List all vulnerabilities"""
    vulns = db.query(Vulnerability).order_by(Vulnerability.discovered_at.desc()).all()
    return vulns


@app.get("/api/vulnerabilities/{vuln_id}", response_model=VulnerabilityResponse)
def get_vulnerability(vuln_id: int, db: Session = Depends(get_db)):
    """Get vulnerability details"""
    vuln = db.query(Vulnerability).filter(Vulnerability.id == vuln_id).first()
    if not vuln:
        raise HTTPException(status_code=404, detail="Vulnerability not found")
    return vuln


# ============================================
# DASHBOARD STATS
# ============================================

@app.get("/api/stats/overview", response_model=OverviewStats)
def get_overview_stats(db: Session = Depends(get_db)):
    """Get dashboard overview statistics"""
    total_targets = db.query(Target).count()
    total_scans = db.query(PentestRun).count()
    total_vulns = db.query(Vulnerability).count()
    critical_vulns = db.query(Vulnerability).filter(Vulnerability.severity == "critical").count()

    recent_scans = db.query(PentestRun).order_by(PentestRun.started_at.desc()).limit(5).all()

    return OverviewStats(
        total_targets=total_targets,
        total_scans=total_scans,
        total_vulnerabilities=total_vulns,
        critical_vulnerabilities=critical_vulns,
        recent_scans=[RunResponse.from_orm(run) for run in recent_scans]
    )


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port, workers=2)
