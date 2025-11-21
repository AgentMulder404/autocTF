from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from enum import Enum

# Enums
class TargetStatus(str, Enum):
    active = "active"
    paused = "paused"
    archived = "archived"

class RunStatus(str, Enum):
    queued = "queued"
    running = "running"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"

class Severity(str, Enum):
    critical = "critical"
    high = "high"
    medium = "medium"
    low = "low"
    info = "info"

# Target Schemas
class TargetCreate(BaseModel):
    name: str
    url: str
    ip_address: Optional[str] = None
    github_repo: Optional[str] = None
    github_branch: Optional[str] = "main"
    repo_owner: Optional[str] = None
    repo_name: Optional[str] = None

class TargetFromGitHub(BaseModel):
    github_url: str

class TargetUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    ip_address: Optional[str] = None
    status: Optional[TargetStatus] = None
    github_repo: Optional[str] = None
    github_branch: Optional[str] = None

class TargetResponse(BaseModel):
    id: int
    name: str
    url: str
    ip_address: Optional[str]
    github_repo: Optional[str]
    github_branch: Optional[str]
    repo_owner: Optional[str]
    repo_name: Optional[str]
    status: str
    created_at: datetime
    last_scan: Optional[datetime]

    class Config:
        from_attributes = True

# Pentest Run Schemas
class RunCreate(BaseModel):
    target_id: int

class RunResponse(BaseModel):
    id: int
    target_id: int
    status: str
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    error_message: Optional[str]

    class Config:
        from_attributes = True

class RunDetailResponse(RunResponse):
    recon_output: Optional[str]
    vulnerabilities_json: Optional[dict]
    vulnerabilities: List["VulnerabilityResponse"] = []

    class Config:
        from_attributes = True

# Vulnerability Schemas
class VulnerabilityResponse(BaseModel):
    id: int
    run_id: int
    type: str
    severity: str
    endpoint: str
    param: Optional[str]
    description: Optional[str]
    exploited: bool
    exploit_output: Optional[str]
    proof_url: Optional[str]
    patched: bool
    created_at: datetime

    class Config:
        from_attributes = True

class VulnerabilityUpdate(BaseModel):
    severity: Optional[Severity] = None
    description: Optional[str] = None
    patched: Optional[bool] = None

# Patch Schemas
class PatchResponse(BaseModel):
    id: int
    vuln_id: int
    file_path: str
    diff: Optional[str]
    pr_url: Optional[str]
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

# Analytics Schemas
class OverviewStats(BaseModel):
    total_targets: int
    active_scans: int
    total_vulnerabilities: int
    critical_vulns: int
    high_vulns: int
    patched_vulns: int
    open_prs: int

class TrendData(BaseModel):
    date: str
    vulnerabilities: int
    patched: int

# Update forward references
RunDetailResponse.model_rebuild()
