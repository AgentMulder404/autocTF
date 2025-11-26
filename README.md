# AutoCTF — Fully Autonomous Pentest + Patch Agent 🚀

**Autonomous penetration testing platform** that finds real vulnerabilities, exploits them, generates patches, and opens PRs with proof—all running in E2B cloud sandboxes.

✅ **No Docker Required** — Runs on macOS 12+, Windows, Linux
✅ **E2B Cloud Sandboxes** — All security scans execute remotely
✅ **GitHub Integration** — Import repos and auto-generate security PRs
✅ **Enterprise Dashboard** — Modern React UI with FastAPI backend

---

## 🎯 Features

- **Automated Reconnaissance**: Parallel nmap, nikto, gobuster scans
- **AI-Powered Analysis**: xAI Grok detects vulnerabilities from scan output
- **Real Exploitation**: Validates findings with sqlmap, custom exploits
- **Auto-Patching**: Generates secure code fixes with LLM
- **PR Creation**: Opens GitHub PRs with proof-of-concept and patches
- **Live Dashboard**: Monitor scans, view vulnerabilities, track patches

---

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Node.js 18+ (for dashboard frontend)
- E2B API key ([sign up free](https://e2b.dev/dashboard))
- xAI API key ([get from x.ai](https://x.ai))
- PostgreSQL database (or [Neon](https://neon.tech) serverless)

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/autocTF.git
cd autocTF
```

### 2. Configure Environment

Create `.env` file with required API keys:

```bash
# Required for pentesting
E2B_API_KEY=e2b_your_key_here
XAI_API_KEY=xai-your_key_here
DATABASE_URL=postgresql://user:pass@host/db

# Optional for PR creation
GITHUB_TOKEN=ghp_your_token_here
GITHUB_REPO=yourusername/your-repo

# Optional for screenshots
BROWSERBASE_API_KEY=bb_live_your_key
BROWSERBASE_PROJECT_ID=your_project_id
```

**Get API Keys:**
- **E2B**: https://e2b.dev/dashboard (100 hours/month free)
- **xAI**: https://x.ai (sign up for API access)
- **GitHub**: https://github.com/settings/tokens (repo, workflow scopes)
- **Neon DB**: https://neon.tech (free serverless PostgreSQL)

### 3. Install Dependencies

```bash
# Backend dependencies
pip install -r requirements.txt
cd dashboard/backend && pip install -r requirements.txt

# Frontend dependencies
cd ../frontend && npm install
cd ../..
```

### 4. Start Dashboard

```bash
# Starts both backend (port 8000) and frontend (port 3000)
./start-dashboard.sh
```

**Access:**
- Dashboard UI: http://localhost:3000
- API Docs: http://localhost:8000/docs

---

## 📖 Usage

### Option 1: Dashboard (Recommended)

1. Open http://localhost:3000
2. Go to **Targets** → **Add Target** → **From GitHub**
3. Paste repo URL: `https://github.com/OWASP/WebGoat`
4. Click **Import from GitHub**
5. Click **Start Scan** on the imported target
6. Monitor progress in **Scans** page
7. View findings in **Vulnerabilities** page

### Option 2: CLI Demo

```bash
# Quick 2-minute demo
./demo_script.sh

# Or run agent directly
python3 agent/main.py
# Enter target URL when prompted
```

### Option 3: API

```bash
# Import GitHub repository
curl -X POST http://localhost:8000/api/targets/from-github \
  -H "Content-Type: application/json" \
  -d '{"github_url": "https://github.com/digininja/DVWA"}'

# Start pentest scan
curl -X POST http://localhost:8000/api/targets/{id}/scan

# Check scan status
curl http://localhost:8000/api/runs/{run_id}

# List vulnerabilities
curl http://localhost:8000/api/vulnerabilities
```

---

## 🏗️ Architecture

```
AutoCTF/
├── agent/                   # Autonomous pentest pipeline
│   ├── main.py             # Orchestrator: recon → analyze → exploit → patch → PR
│   ├── recon.py            # Parallel nmap, nikto, gobuster via E2B
│   ├── analyze.py          # LLM vulnerability detection (xAI Grok)
│   ├── exploit.py          # SQLi, XSS, command injection exploits
│   ├── patcher.py          # LLM-generated security patches
│   └── reporter.py         # Markdown reports + GitHub PR creation
│
├── dashboard/
│   ├── backend/            # FastAPI REST API
│   │   ├── main.py        # API endpoints (targets, scans, vulns)
│   │   ├── models.py      # SQLAlchemy database models
│   │   ├── pentest_worker.py  # Background scan execution
│   │   └── github_utils.py    # GitHub repo import logic
│   │
│   └── frontend/          # React + TailwindCSS dashboard
│       ├── src/pages/     # Dashboard, Targets, Scans, Vulnerabilities
│       └── src/components/# Reusable UI components
│
├── mcp/                    # Model Context Protocol clients
│   ├── exec_client.py     # E2B sandbox command execution
│   ├── browserbase_client.py  # Screenshot capture
│   └── github_client.py   # PR creation with PyGithub
│
├── sandbox_manager.py     # E2B cloud sandbox lifecycle manager
└── startup_validation.py  # Health checks for all services
```

---

## 🔧 Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `E2B_API_KEY` | ✅ Yes | E2B sandbox API key |
| `XAI_API_KEY` | ✅ Yes | xAI Grok LLM API key |
| `DATABASE_URL` | ✅ Yes | PostgreSQL connection string |
| `GITHUB_TOKEN` | ⚠️ Optional | For PR creation (repo scope) |
| `GITHUB_REPO` | ⚠️ Optional | Target repo (owner/name) |
| `BROWSERBASE_API_KEY` | ⚠️ Optional | For screenshots |
| `BROWSERBASE_PROJECT_ID` | ⚠️ Optional | Browserbase project |
| `OPENAI_API_KEY` | ⚠️ Optional | Alternative LLM |

### Database Setup (Neon PostgreSQL)

1. Sign up at https://neon.tech
2. Create new project
3. Copy connection string
4. Add to `.env`:

```bash
DATABASE_URL=postgresql://user:pass@ep-xxx.aws.neon.tech/neondb?sslmode=require
```

---

## 🧪 Testing with WebGoat

**Important**: AutoCTF scans **live web applications**, not just code repositories. For testing with WebGoat:

### Start WebGoat Locally

```bash
# Option 1: Docker
git clone https://github.com/WebGoat/WebGoat.git
cd WebGoat
docker-compose up -d

# Wait 30 seconds for startup
sleep 30
curl http://localhost:8080/WebGoat/  # Should return HTML

# Option 2: Java JAR
wget https://github.com/WebGoat/WebGoat/releases/download/v2023.8/webgoat-2023.8.jar
java -jar webgoat-2023.8.jar --server.port=8080
```

### Scan WebGoat

```bash
# Create target with correct port
curl -X POST http://localhost:8000/api/targets \
  -H "Content-Type: application/json" \
  -d '{
    "name": "WebGoat Live",
    "url": "http://localhost:8080"
  }'

# Start scan
curl -X POST http://localhost:8000/api/targets/{id}/scan
```

**Common Issue**: Scanning `http://localhost:3000` (dashboard UI) instead of `http://localhost:8080` (WebGoat server) will return **0 vulnerabilities** because the target isn't running.

---

## 🐛 Troubleshooting

### Backend Won't Start

```bash
# Check if port 8000 is already in use
lsof -i :8000
kill -9 $(lsof -ti :8000)

# Restart backend
cd dashboard/backend
python3 main.py
```

### E2B Sandbox Errors

```bash
# Verify API key is set
python3 -c "import os; from dotenv import load_dotenv; load_dotenv(); print('E2B_API_KEY:', os.getenv('E2B_API_KEY')[:20])"

# Test sandbox creation
python3 sandbox_manager.py
```

### GitHub Token Issues

- Ensure token has `repo` and `workflow` scopes
- Token format: `ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`
- Get from: https://github.com/settings/tokens

### Database Connection Failed

```bash
# Test Neon connection
psql "$DATABASE_URL" -c "SELECT version();"

# Check connection string format
# Should be: postgresql://user:pass@host.neon.tech/db?sslmode=require
```

---

## 📚 Documentation

- **E2B Migration Guide**: See `E2B_CLOUD_MIGRATION.md` for Docker-free setup details
- **API Documentation**: http://localhost:8000/docs (when backend is running)
- **Project Instructions**: See `CLAUDE.md` for development guidelines

---

## 🎯 Example Workflow

1. **Import Repository**
   Paste `https://github.com/digininja/DVWA` in dashboard

2. **Start Scan**
   AutoCTF clones repo in E2B sandbox and analyzes code

3. **Recon Phase**
   If live URL provided, runs nmap, nikto, gobuster

4. **Analysis**
   xAI Grok analyzes scan output and identifies vulnerabilities

5. **Exploitation**
   Validates findings (e.g., SQLi with sqlmap)

6. **Patching**
   Generates secure code fixes with LLM

7. **PR Creation**
   Opens GitHub PR with proof + patches (if `GITHUB_TOKEN` set)

---

## 🚨 Security Notes

- **E2B Cloud**: All scans run in isolated cloud sandboxes
- **No Local Docker**: No container runtime needed on your machine
- **API Keys**: Keep `.env` file secure, never commit to git
- **Rate Limits**: E2B free tier = 100 hours/month
- **Target Authorization**: Only scan systems you own or have permission to test

---

## 📊 System Requirements

- **OS**: macOS 12+, Windows 10+, Linux (Ubuntu 20.04+)
- **Python**: 3.9 or higher
- **Node.js**: 18 or higher (for dashboard)
- **RAM**: 2GB minimum, 4GB recommended
- **Network**: Stable internet (E2B cloud access)

---

## 🤝 Contributing

Issues and PRs welcome! Please ensure:
- Code follows existing patterns
- Tests pass before submitting
- Environment variables are documented

---

## 📄 License

MIT License - See LICENSE file for details

---

## 🙏 Acknowledgments

- **E2B** - Cloud sandbox infrastructure
- **xAI** - Grok LLM for vulnerability analysis
- **OWASP** - WebGoat and DVWA test applications
- **PyGithub** - GitHub API integration

---

## 🔗 Links

- **E2B Dashboard**: https://e2b.dev/dashboard
- **xAI Platform**: https://x.ai
- **Neon Database**: https://neon.tech
- **GitHub Tokens**: https://github.com/settings/tokens

---

**Built for security researchers, penetration testers, and DevSecOps teams.**
