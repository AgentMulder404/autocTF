# 🎯 SQLMap DB Dump + Screenshot + PR Feature

## Overview
Enhanced AutoCTF with **real SQLi exploitation** including full database dumps, visual proof, and comprehensive PR documentation.

## What's New

### 1. **Real SQLmap Exploitation** (`agent/exploit.py`)
- **Full DB enumeration**: Discovers all databases on the target
- **Complete data dump**: Extracts tables, columns, and data
- **Credential extraction**: Attempts to extract password hashes and credentials
- **Multi-step exploitation**:
  1. Test for SQLi vulnerability
  2. Enumerate databases (`--dbs`)
  3. Dump database contents (`--dump`)
  4. Extract passwords (`--passwords`)

### 2. **HTML Visualization + Screenshots** (`agent/exploit.py`)
- Creates styled HTML report of DB dump with:
  - **Hacker theme**: Terminal-style green on black
  - **Database list**: All compromised databases
  - **Credentials section**: Extracted passwords/hashes
  - **Exploitation summary**: Quick stats
  - **Raw output**: Full sqlmap output (truncated)
- Screenshots HTML using Browserbase for proof
- Stores screenshots in vulnerability records

### 3. **Enhanced GitHub PRs** (`mcp/github_client.py`)
- PRs now include:
  - 🎯 **Exploitation evidence**: Real DB dump data
  - 💾 **Database list**: All compromised databases
  - 🔑 **Credentials extracted**: Count and sample
  - 📸 **Screenshots**: Visual proof embedded in PR
  - 🛡️ **Remediation steps**: Action items for devs
  - 🚨 **Severity warnings**: Clear CRITICAL alerts

### 4. **Advanced Patches** (`dashboard/backend/pentest_worker.py`)
- Patches include:
  - Exploitation context (which DBs were accessed)
  - Credential count found
  - Prepared statement examples
  - Input validation functions
  - Immediate action checklist

### 5. **Database Schema Updates** (`models.py`, `schemas.py`)
Added fields to Vulnerability model:
- `dump_data` (JSON): Full DB dump results
- `title` (String): Vulnerability title
- `proof` (Text): Proof of exploitation
- `cvss_score` (String): CVSS score if available

## How It Works

### Exploitation Flow
```
1. Recon Phase
   └─> Discover endpoints and parameters

2. Vulnerability Detection
   └─> LLM analyzes recon output

3. SQLi Exploitation (NEW!)
   ├─> Test for SQLi
   ├─> Enumerate databases
   ├─> Dump all data
   ├─> Extract credentials
   └─> Save results

4. Screenshot Generation (NEW!)
   ├─> Create HTML visualization
   ├─> Style with hacker theme
   ├─> Capture screenshot via Browserbase
   └─> Store URL in database

5. Patch Generation
   ├─> Generate secure code
   ├─> Include exploitation context
   └─> Add action items

6. PR Creation (ENHANCED!)
   ├─> Create branch
   ├─> Upload patched files
   ├─> Embed screenshots
   ├─> Add DB dump evidence
   └─> Generate comprehensive PR body
```

### Example PR Structure
```markdown
# 🎯 AutoCTF Security Patch

## 🔥 EXPLOITATION EVIDENCE

### 💀 SQLi Exploitation Summary
- Tables dumped: 5
- Databases compromised: dvwa, information_schema
- Credentials extracted

### 💾 Databases Compromised
- ✅ `dvwa` - **DUMPED**
- ✅ `testdb` - **DUMPED**

### 🔑 Credentials Extracted
⚠️ 12 credential entries found

### 📸 Proof of Exploitation
![Screenshot 1](https://...)

## 🛡️ REMEDIATION
[Action items and remediation steps]
```

## Database Migration

### Option 1: Automatic Migration (Alembic)
```bash
# Generate migration
alembic revision --autogenerate -m "Add exploitation fields"

# Apply migration
alembic upgrade head
```

### Option 2: Manual SQL (PostgreSQL/Neon)
```sql
ALTER TABLE vulnerabilities
ADD COLUMN dump_data JSON,
ADD COLUMN cvss_score VARCHAR(10),
ADD COLUMN title VARCHAR(255),
ADD COLUMN proof TEXT;
```

### Option 3: Recreate Database (Development Only)
```bash
# WARNING: This will delete all data
rm dashboard/backend/*.db  # If using SQLite
python -c "from dashboard.backend.database import init_db; init_db()"
```

## Configuration

### Required Environment Variables
```bash
# Existing
E2B_API_KEY=your_e2b_key
OPENAI_API_KEY=your_openai_key
GITHUB_TOKEN=your_github_token
GITHUB_REPO=username/repo

# Screenshot capture
BROWSERBASE_API_KEY=your_browserbase_key
BROWSERBASE_PROJECT_ID=your_project_id

# Database (Neon PostgreSQL)
DATABASE_URL=postgresql://user:pass@host/db
```

## Usage

### Run Full Pentest with DB Dump
```bash
# Start dashboard
./start-dashboard.sh

# In dashboard UI:
1. Add target
2. Start scan
3. Wait for completion
4. View summary report (now with DB dump details!)
5. Check GitHub for PR with screenshots
```

### CLI Mode (Standalone)
```bash
# Run against DVWA
cd vulnerable-app && docker compose up -d
python agent/main.py
```

## Features in Action

### 1. Console Output
```
🔍 Testing SQLi on http://target/login.php?id=...
✅ SQLi vulnerability CONFIRMED!
📊 Enumerating databases...
💾 Dumping database contents...
🔑 Extracting credentials...
✅ SQLi exploitation complete! Dumped 3 databases
📸 Creating dump screenshot...
✅ Screenshot saved: /tmp/sqlmap_dumps/dump_20250121_143022.html
```

### 2. HTML Report
- Dark terminal theme (green on black)
- Organized sections:
  - Exploitation summary
  - Database list
  - Credentials (in expandable section)
  - Dump files
  - Raw output

### 3. GitHub PR
- Title: `🚨 [AutoCTF] CRITICAL: SQLi Patched for MyApp`
- Body includes:
  - Scan details
  - Exploitation evidence
  - Screenshot embeds
  - DB dump statistics
  - Remediation checklist

## Technical Details

### SQLmap Flags Used
```bash
# Detection
--batch --risk=2 --level=2 --technique=BEUSTQ --threads=5

# Database enumeration
--dbs --threads=5

# Data dump
--dump --threads=5 --dump-format=JSON --output-dir=/tmp/sqlmap_dumps

# Credential extraction
--passwords --threads=5
```

### Screenshot Generation
- HTML file created in `/tmp/sqlmap_dumps/`
- Browserbase session created
- Screenshot captured of HTML file
- URL stored in `vulnerability.proof_url`

### Data Storage
```python
# Vulnerability record
{
    "type": "SQLi",
    "exploited": True,
    "title": "SQL Injection on /login.php",
    "proof": "DB Dump successful - 3 databases accessed",
    "proof_url": "https://browserbase.com/...",
    "dump_data": {
        "databases": ["dvwa", "testdb"],
        "credential_count": 12,
        "summary": "🎯 SQLi EXPLOITATION SUCCESSFUL...",
        "timestamp": "2025-01-21T14:30:22.123Z"
    }
}
```

## Security Considerations

### Handling Sensitive Data
- ⚠️ **Credentials are extracted**: Be careful with test data
- 🔒 **Screenshots contain data**: Ensure Browserbase privacy settings
- 🗄️ **DB dumps stored**: Consider encryption for `dump_data` field
- 🔐 **PR visibility**: Private repos recommended

### Best Practices
1. Use test databases with fake data
2. Rotate all credentials after testing
3. Delete screenshots after demo
4. Clear sqlmap output directory: `/tmp/sqlmap_dumps/`

## Troubleshooting

### Issue: SQLmap not found
```bash
# Install sqlmap
apt-get install sqlmap  # Linux
brew install sqlmap     # macOS
pip install sqlmap-python
```

### Issue: Screenshots not capturing
- Check Browserbase API key
- Verify project ID
- Test Browserbase connection:
```python
from mcp.browserbase_client import create_session
session = create_session()
print(session.session_id)
```

### Issue: Database migration errors
```bash
# Reset database (dev only!)
rm *.db
python -c "from database import init_db; init_db()"
```

### Issue: PR creation fails
- Verify GitHub token has repo write access
- Check repo name format: `owner/repo`
- Ensure base branch exists (main/master)

## Future Enhancements

- [ ] Support for other vuln types (XSS, CSRF, etc.)
- [ ] Video recording of exploitation
- [ ] Automatic credential cracking (with permission)
- [ ] Interactive HTML reports with search
- [ ] Export to PDF
- [ ] Integration with vulnerability databases (NVD, CVE)
- [ ] Slack/Discord notifications with screenshots
- [ ] Auto-merge PRs after CI passes

## Credits

Built with:
- **sqlmap**: Legendary SQLi tool
- **E2B**: Sandboxed code execution
- **Browserbase**: Browser automation & screenshots
- **PyGithub**: GitHub API wrapper
- **FastAPI + React**: Dashboard framework

---

🤖 **AutoCTF** - Because manual pentesting is so 2023
