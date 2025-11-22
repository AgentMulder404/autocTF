from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class Target(Base):
    __tablename__ = "targets"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    url = Column(String(512), nullable=False)
    ip_address = Column(String(50))
    github_repo = Column(String(512), nullable=True)  # GitHub repo URL
    github_branch = Column(String(100), default="main")  # Default branch
    repo_owner = Column(String(255), nullable=True)  # GitHub username/org
    repo_name = Column(String(255), nullable=True)  # Repository name
    status = Column(String(50), default="active")  # active, paused, archived
    created_at = Column(DateTime, default=datetime.utcnow)
    last_scan = Column(DateTime, nullable=True)

    # Relationships
    runs = relationship("PentestRun", back_populates="target", cascade="all, delete-orphan")

class PentestRun(Base):
    __tablename__ = "pentest_runs"

    id = Column(Integer, primary_key=True)
    target_id = Column(Integer, ForeignKey("targets.id"), nullable=False)
    status = Column(String(50), default="queued")  # queued, running, completed, failed, cancelled
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    recon_output = Column(Text, nullable=True)
    vulnerabilities_json = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)

    # Relationships
    target = relationship("Target", back_populates="runs")
    vulnerabilities = relationship("Vulnerability", back_populates="run", cascade="all, delete-orphan")

class Vulnerability(Base):
    __tablename__ = "vulnerabilities"

    id = Column(Integer, primary_key=True)
    run_id = Column(Integer, ForeignKey("pentest_runs.id"), nullable=False)
    type = Column(String(100), nullable=False)  # SQLi, XSS, CSRF, etc.
    severity = Column(String(50), default="medium")  # critical, high, medium, low, info
    endpoint = Column(String(512), nullable=False)
    param = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    exploited = Column(Boolean, default=False)
    exploit_output = Column(Text, nullable=True)
    proof_url = Column(String(512), nullable=True)
    patched = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Enhanced exploitation data
    dump_data = Column(JSON, nullable=True)  # Store full DB dump results (databases, credentials, etc.)
    cvss_score = Column(String(10), nullable=True)  # CVSS score if available
    title = Column(String(255), nullable=True)  # Vulnerability title
    proof = Column(Text, nullable=True)  # Proof of concept/exploitation evidence

    # Relationships
    run = relationship("PentestRun", back_populates="vulnerabilities")
    patches = relationship("Patch", back_populates="vulnerability", cascade="all, delete-orphan")

class Patch(Base):
    __tablename__ = "patches"

    id = Column(Integer, primary_key=True)
    vuln_id = Column(Integer, ForeignKey("vulnerabilities.id"), nullable=False)
    file_path = Column(String(512), nullable=False)
    diff = Column(Text, nullable=True)
    pr_url = Column(String(512), nullable=True)
    status = Column(String(50), default="pending")  # pending, created, merged, rejected
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    vulnerability = relationship("Vulnerability", back_populates="patches")
