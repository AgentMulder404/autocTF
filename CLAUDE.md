# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AutoCTF is an autonomous penetration testing and patching agent. It automatically:
1. Spins up a vulnerable target (DVWA via Docker)
2. Runs reconnaissance scans (nmap, gobuster, nikto)
3. Analyzes scan results with LLM to identify vulnerabilities
4. Exploits confirmed vulnerabilities (e.g., SQLi with sqlmap)
5. Generates patches and opens a GitHub PR

## Commands

### Run Enterprise Dashboard (Recommended)
```bash
./start-dashboard.sh
# Dashboard: http://localhost:3000
# API Docs: http://localhost:8000/docs
```

### Run CLI Demo
```bash
./demo_script.sh
# Or manually:
docker compose -f vulnerable-app/docker-compose.yml up -d
python -u agent/main.py
```

### Install Dependencies
```bash
# Core dependencies
pip install -r requiremnets.txt

# Dashboard backend
pip install -r dashboard/backend/requirements.txt

# Dashboard frontend
cd dashboard/frontend && npm install
```

### Start Vulnerable Target Only
```bash
docker compose -f vulnerable-app/docker-compose.yml up -d
# Target available at http://localhost:8080
```

## Architecture

### Agent Pipeline (`agent/`)
- `main.py` - Orchestrates the full pentest pipeline: recon → analyze → exploit → patch → PR
- `recon.py` - Parallel reconnaissance using nmap, gobuster, nikto via E2B sandbox
- `analyze.py` - LLM-powered vulnerability detection from scan output (uses OpenAI/Groq)
- `exploit.py` - Exploitation modules (currently SQLi via sqlmap)
- `patcher.py` - LLM-generated security patches for found vulnerabilities
- `reporter.py` - Generates markdown reports with proofs and diffs

### MCP Clients (`mcp/`)
- `exec_client.py` - E2B sandbox for running security tools (nmap, sqlmap, etc.)
- `browserbase_client.py` - Browserbase integration for screenshots/browser automation
- `github_client.py` - PyGithub wrapper for creating branches and PRs

### Test Target (`vulnerable-app/`)
- Docker Compose setup for DVWA (Damn Vulnerable Web Application)

### Enterprise Dashboard (`dashboard/`)
- **Backend (FastAPI)**: REST API for managing targets, scans, and vulnerabilities
  - `models.py` - SQLAlchemy database models
  - `schemas.py` - Pydantic schemas for API validation
  - `main.py` - FastAPI application with all endpoints
  - `database.py` - Database connection and session management
  - `pentest_worker.py` - Background worker for running pentests
- **Frontend (React)**: Modern web UI for dashboard
  - `src/pages/` - Dashboard, Targets, Scans, Vulnerabilities pages
  - `src/components/` - Reusable UI components
  - `src/lib/api.js` - API client functions

## Environment Variables

Required in `.env`:
- `E2B_API_KEY` - For E2B sandbox execution of security tools
- `OPENAI_API_KEY` - For LLM analysis (or configure Groq in analyze.py)
- `BROWSERBASE_API_KEY` / `BROWSERBASE_PROJECT_ID` - For screenshot capture
- `GITHUB_TOKEN` / `GITHUB_REPO` - For PR creation
- `DATABASE_URL` - Database connection (optional, defaults to SQLite)
