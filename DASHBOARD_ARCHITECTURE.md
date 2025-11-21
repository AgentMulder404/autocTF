# AutoCTF Enterprise Dashboard Architecture

## Overview
Enterprise-grade web dashboard for managing autonomous penetration tests, viewing results, and tracking security posture across multiple targets.

## Architecture Components

### 1. Backend (Python FastAPI)
- **API Server**: RESTful API for dashboard operations
- **Task Queue**: Celery for async pentest job management
- **WebSocket**: Real-time status updates during scans
- **Database**: SQLite (dev) / PostgreSQL (production)

### 2. Frontend (React + Tailwind CSS)
- **Dashboard View**: Overview of all pentest runs
- **Target Management**: Add/edit/delete targets
- **Live Console**: Real-time scan output
- **Report Viewer**: View findings with screenshots
- **PR Tracker**: Monitor auto-generated patches

### 3. Database Schema

```sql
-- Targets table
targets (
  id, name, url, ip_address, status, created_at, last_scan
)

-- Pentest runs
pentest_runs (
  id, target_id, status, started_at, completed_at,
  recon_output, vulnerabilities_json
)

-- Vulnerabilities
vulnerabilities (
  id, run_id, type, severity, endpoint, param,
  exploited, patched, proof_url
)

-- Patches
patches (
  id, vuln_id, file_path, diff, pr_url, status
)
```

## Key Features

### For Security Teams
1. **Multi-Target Management**: Scan multiple applications
2. **Scheduled Scans**: Cron-based recurring pentests
3. **Vulnerability Tracking**: Track findings over time
4. **Compliance Reports**: Export findings for audits
5. **Team Collaboration**: Comments and assignment

### For Developers
1. **Auto-Patch PRs**: GitHub integration
2. **Remediation Tracking**: Monitor fix status
3. **Historical Trends**: Vuln counts over time
4. **CVSS Scoring**: Severity classification

### For Management
1. **Executive Dashboard**: High-level metrics
2. **Risk Scoring**: Overall security posture
3. **Export Reports**: PDF/CSV generation
4. **SLA Tracking**: Time to remediation

## API Endpoints

### Targets
- `GET /api/targets` - List all targets
- `POST /api/targets` - Add new target
- `GET /api/targets/{id}` - Get target details
- `PUT /api/targets/{id}` - Update target
- `DELETE /api/targets/{id}` - Remove target

### Pentest Runs
- `POST /api/targets/{id}/scan` - Start pentest
- `GET /api/runs` - List all runs
- `GET /api/runs/{id}` - Get run details
- `GET /api/runs/{id}/status` - Real-time status
- `DELETE /api/runs/{id}` - Cancel run

### Vulnerabilities
- `GET /api/vulnerabilities` - List all vulns
- `GET /api/vulnerabilities/{id}` - Get vuln details
- `PUT /api/vulnerabilities/{id}` - Update status
- `POST /api/vulnerabilities/{id}/patch` - Generate patch

### Reports
- `GET /api/reports/{run_id}` - Get report
- `GET /api/reports/{run_id}/pdf` - Export PDF
- `GET /api/reports/{run_id}/csv` - Export CSV

### Analytics
- `GET /api/analytics/overview` - Dashboard stats
- `GET /api/analytics/trends` - Historical trends
- `GET /api/analytics/risk-score` - Risk metrics

## Tech Stack

### Backend
- FastAPI (REST API)
- SQLAlchemy (ORM)
- Celery (Task Queue)
- Redis (Message Broker)
- WebSockets (Real-time)

### Frontend
- React 18
- Tailwind CSS
- Shadcn/ui Components
- Recharts (Analytics)
- React Query (State)
- Socket.io (WebSocket)

### DevOps
- Docker Compose
- Nginx (Reverse Proxy)
- PostgreSQL (Production DB)

## Security Considerations
- JWT authentication
- Role-based access control (RBAC)
- API rate limiting
- Audit logging
- Encrypted credentials storage
