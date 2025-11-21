# AutoCTF Enterprise Dashboard

A modern web-based dashboard for managing autonomous penetration testing operations.

## Features

- **Target Management**: Add, edit, and manage pentest targets
- **Automated Scanning**: One-click pentesting with real-time status updates
- **Vulnerability Tracking**: Comprehensive vulnerability management and tracking
- **Auto-Patching**: Automatic PR generation with security fixes
- **Analytics Dashboard**: Real-time metrics and trends visualization
- **Enterprise-Ready**: Multi-target support with role-based access control

## Quick Start

### Option 1: Docker Compose (Recommended)

```bash
# Start all services
cd dashboard
docker-compose up -d

# Access the dashboard
open http://localhost:3000

# API documentation
open http://localhost:8000/docs
```

### Option 2: Manual Setup

**Backend:**
```bash
cd dashboard/backend
pip install -r requirements.txt
python main.py
```

**Frontend:**
```bash
cd dashboard/frontend
npm install
npm run dev
```

## Architecture

### Backend (FastAPI)
- REST API with auto-generated OpenAPI docs
- SQLAlchemy ORM with Neon PostgreSQL
- Background task processing for pentests
- Real-time status updates

### Frontend (React + Tailwind)
- Modern React 18 with hooks
- Tailwind CSS for styling
- React Query for state management
- Recharts for analytics visualization

## API Endpoints

### Targets
- `GET /api/targets` - List all targets
- `POST /api/targets` - Create target
- `PUT /api/targets/{id}` - Update target
- `DELETE /api/targets/{id}` - Delete target
- `POST /api/targets/{id}/scan` - Start pentest

### Scans
- `GET /api/runs` - List all scan runs
- `GET /api/runs/{id}` - Get run details
- `GET /api/runs/{id}/status` - Real-time status
- `DELETE /api/runs/{id}` - Cancel run

### Vulnerabilities
- `GET /api/vulnerabilities` - List all vulnerabilities
- `GET /api/vulnerabilities/{id}` - Get vulnerability details
- `PUT /api/vulnerabilities/{id}` - Update vulnerability

### Analytics
- `GET /api/analytics/overview` - Dashboard statistics
- `GET /api/analytics/trends` - Historical trends

## Configuration

Set these environment variables in `../../.env`:

```env
# E2B for sandbox execution
E2B_API_KEY=your_key

# OpenAI for LLM analysis
OPENAI_API_KEY=your_key

# Browserbase for screenshots
BROWSERBASE_API_KEY=your_key
BROWSERBASE_PROJECT_ID=your_project_id

# GitHub for PR creation
GITHUB_TOKEN=your_token
GITHUB_REPO=username/repo

# Neon PostgreSQL Database (required)
DATABASE_URL=postgresql://user:password@host/database?sslmode=require
```

### Database Setup (Neon PostgreSQL)

This project uses [Neon](https://neon.tech) serverless PostgreSQL:

1. **Create a Neon account** at https://neon.tech
2. **Create a new project** in the Neon console
3. **Copy the connection string** from your project dashboard
4. **Add to `.env`**:
   ```env
   DATABASE_URL=postgresql://user:password@ep-xxx.aws.neon.tech/neondb?sslmode=require
   ```
5. **Database tables are auto-created** on first run via SQLAlchemy migrations

**Features:**
- Connection pooling (5 connections, max 10)
- Automatic connection health checks
- SSL/TLS enabled by default
- No local PostgreSQL installation needed

## Development

**Backend:**
```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend:**
```bash
cd frontend
npm run dev
```

## Production Deployment

1. Neon database is already production-ready (serverless, auto-scaling)
2. Update CORS origins in `backend/main.py`
3. Build frontend: `npm run build`
4. Use Nginx as reverse proxy
5. Enable SSL/TLS certificates
6. Configure authentication and RBAC
7. Consider increasing Neon connection pool size for higher load

## Security Considerations

- API authentication (JWT recommended)
- Rate limiting on API endpoints
- Input validation and sanitization
- Secure credential storage
- Audit logging
- HTTPS in production
