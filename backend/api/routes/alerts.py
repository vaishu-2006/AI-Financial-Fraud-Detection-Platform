"""
Alerts and Notifications Routes
"""
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from pydantic import BaseModel
from enum import Enum

from api.middleware.auth import TokenData, require_roles, UserRole

router = APIRouter()

class AlertType(str, Enum):
    HIGH_RISK = "high_risk"
    ANOMALY = "anomaly"
    VELOCITY = "velocity"
    PATTERN = "pattern"
    THRESHOLD = "threshold"

class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AlertStatus(str, Enum):
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"
    FALSE_POSITIVE = "false_positive"
    ESCALATED = "escalated"

class AlertSummary(BaseModel):
    id: str
    alert_type: str
    severity: str
    title: str
    status: str
    risk_score: Optional[float]
    created_at: str
    assigned_to: Optional[str]

class AlertDetail(AlertSummary):
    description: Optional[str]
    transaction_ids: List[str]
    model_id: Optional[str]
    anomaly_score: Optional[float]
    priority: int
    resolved_by: Optional[str]
    resolved_at: Optional[str]
    resolution_notes: Optional[str]
    assigned_at: Optional[str]

class AlertUpdate(BaseModel):
    status: Optional[AlertStatus] = None
    assigned_to: Optional[str] = None
    resolution_notes: Optional[str] = None
    resolution_type: Optional[str] = None
    priority: Optional[int] = None

class AlertStats(BaseModel):
    total_open: int
    by_severity: dict
    by_type: dict
    avg_resolution_time_hours: float

@router.get("", response_model=List[AlertSummary])
async def list_alerts(
    request: Request,
    status: Optional[AlertStatus] = None,
    severity: Optional[Severity] = None,
    alert_type: Optional[AlertType] = None,
    assigned_to_me: bool = False,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    token_data: TokenData = Depends(require_roles([UserRole.ANALYST, UserRole.MANAGER, UserRole.ADMIN]))
):
    """List alerts with filtering options."""
    supabase = request.app.state.supabase

    query = supabase.table("alerts").select("*").order("created_at", desc=True)
    offset = (page - 1) * page_size

    if status:
        query = query.eq("status", status.value)
    if severity:
        query = query.eq("severity", severity.value)
    if alert_type:
        query = query.eq("alert_type", alert_type.value)
    if assigned_to_me:
        query = query.eq("assigned_to", token_data.user_id)

    query = query.range(offset, offset + page_size - 1)
    result = query.execute()

    return result.data

@router.get("/stats", response_model=AlertStats)
async def get_alert_stats(request: Request):
    """Get alert statistics summary."""
    supabase = request.app.state.supabase

    # Get open alerts
    open_alerts = supabase.table("alerts").select("*").in_("status", ["open", "acknowledged", "investigating"]).execute()

    data = open_alerts.data or []

    by_severity = {}
    by_type = {}
    for alert in data:
        sev = alert.get("severity", "unknown")
        by_severity[sev] = by_severity.get(sev, 0) + 1
        at = alert.get("alert_type", "unknown")
        by_type[at] = by_type.get(at, 0) + 1

    # Calculate avg resolution time
    resolved = supabase.table("alerts").select("created_at, resolved_at").eq("status", "resolved").limit(100).execute()
    resolution_times = []
    for a in resolved.data or []:
        if a.get("resolved_at"):
            created = datetime.fromisoformat(a["created_at"].replace("Z", "+00:00"))
            resolved_time = datetime.fromisoformat(a["resolved_at"].replace("Z", "+00:00"))
            hours = (resolved_time - created).total_seconds() / 3600
            resolution_times.append(hours)

    avg_resolution = sum(resolution_times) / len(resolution_times) if resolution_times else 0

    return AlertStats(
        total_open=len(data),
        by_severity=by_severity,
        by_type=by_type,
        avg_resolution_time_hours=round(avg_resolution, 2)
    )

@router.get("/{alert_id}", response_model=AlertDetail)
async def get_alert(
    alert_id: str,
    request: Request,
    token_data: TokenData = Depends(require_roles([UserRole.ANALYST, UserRole.MANAGER, UserRole.ADMIN]))
):
    """Get detailed alert information."""
    supabase = request.app.state.supabase

    result = supabase.table("alerts").select("*").eq("id", alert_id).maybe_single().execute()

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )

    return result.data

@router.patch("/{alert_id}", response_model=AlertDetail)
async def update_alert(
    alert_id: str,
    update: AlertUpdate,
    request: Request,
    token_data: TokenData = Depends(require_roles([UserRole.ANALYST, UserRole.MANAGER, UserRole.ADMIN]))
):
    """Update alert status, assignment, or add resolution notes."""
    supabase = request.app.state.supabase

    update_data = update.model_dump(exclude_unset=True)

    if update.status in [AlertStatus.RESOLVED, AlertStatus.FALSE_POSITIVE]:
        update_data["resolved_by"] = token_data.user_id
        update_data["resolved_at"] = datetime.utcnow().isoformat()

    if update.assigned_to and "assigned_at" not in update_data:
        update_data["assigned_at"] = datetime.utcnow().isoformat()

    result = supabase.table("alerts").update(update_data).eq("id", alert_id).execute()

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )

    return result.data[0]

@router.post("/{alert_id}/escalate")
async def escalate_alert(
    alert_id: str,
    request: Request,
    token_data: TokenData = Depends(require_roles([UserRole.ANALYST, UserRole.MANAGER, UserRole.ADMIN]))
):
    """Escalate an alert to manager review."""
    supabase = request.app.state.supabase

    # Get managers
    managers = supabase.table("users").select("id").eq("role", "manager").eq("is_active", True).limit(1).execute()

    assigned_to = managers.data[0]["id"] if managers.data else None

    result = supabase.table("alerts").update({
        "status": "escalated",
        "priority": 10,
        "assigned_to": assigned_to
    }).eq("id", alert_id).execute()

    return {"message": "Alert escalated", "assigned_to": assigned_to}

@router.post("/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str,
    request: Request,
    token_data: TokenData = Depends(require_roles([UserRole.ANALYST, UserRole.MANAGER, UserRole.ADMIN]))
):
    """Acknowledge an alert (mark as being reviewed)."""
    supabase = request.app.state.supabase

    result = supabase.table("alerts").update({
        "status": "acknowledged",
        "assigned_to": token_data.user_id
    }).eq("id", alert_id).execute()

    return {"message": "Alert acknowledged"}
