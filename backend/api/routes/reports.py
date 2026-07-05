"""
Reports and Analytics Routes
"""
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import json
import io

from api.middleware.auth import TokenData, require_roles, UserRole

router = APIRouter()

class DashboardMetrics(BaseModel):
    total_transactions: int
    fraud_detected: int
    false_positives: int
    detection_rate: float
    avg_risk_score: float
    total_amount_monitored: float
    fraud_amount_prevented: float

class RiskDistribution(BaseModel):
    safe: int
    suspicious: int
    fraudulent: int

class TimeSeriesPoint(BaseModel):
    date: str
    volume: int
    fraud_count: int
    avg_amount: float

class ModelPerformance(BaseModel):
    model_id: str
    model_type: str
    precision: float
    recall: float
    f1_score: float
    predictions_made: int

class ReportGenerate(BaseModel):
    report_type: str
    start_date: str
    end_date: str
    format: str = "json"

@router.get("/dashboard", response_model=DashboardMetrics)
async def get_dashboard_metrics(
    request: Request,
    days: int = Query(7, ge=1, le=90),
    token_data: TokenData = Depends(require_roles([UserRole.ANALYST, UserRole.MANAGER, UserRole.ADMIN]))
):
    """Get key metrics for the dashboard overview."""
    supabase = request.app.state.supabase

    start_date = (datetime.utcnow() - timedelta(days=days)).isoformat()

    # Get transactions
    tx_result = supabase.table("transactions").select("id, amount, risk_label, status, risk_score").gte("created_at", start_date).execute()

    transactions = tx_result.data or []

    total = len(transactions)
    fraud_detected = sum(1 for t in transactions if t.get("risk_label") == "fraudulent")
    suspicious = sum(1 for t in transactions if t.get("risk_label") == "suspicious")
    false_positives = sum(1 for t in transactions if t.get("status") == "rejected" and t.get("risk_label") != "fraudulent")

    total_amount = sum(float(t.get("amount", 0)) for t in transactions)
    fraud_amount = sum(float(t.get("amount", 0)) for t in transactions if t.get("risk_label") == "fraudulent")
    risk_scores = [t.get("risk_score", 0) for t in transactions if t.get("risk_score") is not None]

    return DashboardMetrics(
        total_transactions=total,
        fraud_detected=fraud_detected,
        false_positives=false_positives,
        detection_rate=fraud_detected / total if total > 0 else 0,
        avg_risk_score=sum(risk_scores) / len(risk_scores) if risk_scores else 0,
        total_amount_monitored=total_amount,
        fraud_amount_prevented=fraud_amount
    )

@router.get("/risk-distribution", response_model=RiskDistribution)
async def get_risk_distribution(
    request: Request,
    days: int = Query(30, ge=1, le=90),
    token_data: TokenData = Depends(require_roles([UserRole.ANALYST, UserRole.MANAGER, UserRole.ADMIN]))
):
    """Get distribution of risk labels."""
    supabase = request.app.state.supabase

    start_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
    result = supabase.table("transactions").select("risk_label").gte("created_at", start_date).execute()

    data = result.data or []
    dist = {"safe": 0, "suspicious": 0, "fraudulent": 0}
    for tx in data:
        label = tx.get("risk_label")
        if label in dist:
            dist[label] += 1

    return RiskDistribution(**dist)

@router.get("/timeseries", response_model=List[TimeSeriesPoint])
async def get_timeseries_data(
    request: Request,
    days: int = Query(30, ge=1, le=90),
    granularity: str = Query("day", pattern="^(day|hour)$"),
    token_data: TokenData = Depends(require_roles([UserRole.ANALYST, UserRole.MANAGER, UserRole.ADMIN]))
):
    """Get transaction volume and fraud trends over time."""
    supabase = request.app.state.supabase

    start_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
    result = supabase.table("transactions").select("transaction_timestamp, amount, risk_label").gte("transaction_timestamp", start_date).order("transaction_timestamp").execute()

    # Group by day
    data = result.data or []
    daily_data = {}

    for tx in data:
        ts = tx.get("transaction_timestamp", "")
        if granularity == "day":
            key = ts[:10] if len(ts) >= 10 else "unknown"
        else:
            key = ts[:13] if len(ts) >= 13 else "unknown"

        if key not in daily_data:
            daily_data[key] = {"volume": 0, "fraud_count": 0, "amounts": []}

        daily_data[key]["volume"] += 1
        if tx.get("risk_label") == "fraudulent":
            daily_data[key]["fraud_count"] += 1
        daily_data[key]["amounts"].append(float(tx.get("amount", 0)))

    timeseries = []
    for date, stats in sorted(daily_data.items()):
        timeseries.append(TimeSeriesPoint(
            date=date,
            volume=stats["volume"],
            fraud_count=stats["fraud_count"],
            avg_amount=sum(stats["amounts"]) / len(stats["amounts"]) if stats["amounts"] else 0
        ))

    return timeseries

@router.get("/model-performance", response_model=List[ModelPerformance])
async def get_model_performance(request: Request):
    """Compare performance metrics across all trained models."""
    supabase = request.app.state.supabase

    result = supabase.table("models").select("id, model_type, precision_score, recall_score, f1_score, roc_auc").neq("status", "training").order("trained_at", desc=True).limit(10).execute()

    models = result.data or []

    # Get prediction counts
    for model in models:
        pred_count = supabase.table("transactions").select("id", count="exact").eq("model_id", model["id"]).execute()
        model["predictions_made"] = pred_count.count if pred_count.count else 0

    return [
        ModelPerformance(
            model_id=m["id"],
            model_type=m["model_type"],
            precision=m.get("precision_score") or 0,
            recall=m.get("recall_score") or 0,
            f1_score=m.get("f1_score") or 0,
            predictions_made=m.get("predictions_made", 0)
        )
        for m in models
    ]

@router.get("/top-merchants")
async def get_top_merchants(
    request: Request,
    limit: int = Query(10, ge=1, le=50),
    sort_by: str = Query("volume", pattern="^(volume|fraud_rate|amount)$"),
    token_data: TokenData = Depends(require_roles([UserRole.ANALYST, UserRole.MANAGER, UserRole.ADMIN]])
):
    """Get statistics for top merchants by various criteria."""
    supabase = request.app.state.supabase

    result = supabase.table("transactions").select("merchant_id, merchant_name, amount, risk_label").limit(10000).execute()

    data = result.data or []
    merchant_stats = {}

    for tx in data:
        mid = tx.get("merchant_id")
        if not mid:
            continue

        if mid not in merchant_stats:
            merchant_stats[mid] = {
                "merchant_id": mid,
                "merchant_name": tx.get("merchant_name", "Unknown"),
                "volume": 0,
                "total_amount": 0,
                "fraud_count": 0
            }

        merchant_stats[mid]["volume"] += 1
        merchant_stats[mid]["total_amount"] += float(tx.get("amount", 0))
        if tx.get("risk_label") == "fraudulent":
            merchant_stats[mid]["fraud_count"] += 1

    # Calculate fraud rate and sort
    for stats in merchant_stats.values():
        stats["fraud_rate"] = stats["fraud_count"] / stats["volume"] if stats["volume"] > 0 else 0

    if sort_by == "volume":
        sorted_merchants = sorted(merchant_stats.values(), key=lambda x: x["volume"], reverse=True)
    elif sort_by == "fraud_rate":
        sorted_merchants = sorted(merchant_stats.values(), key=lambda x: x["fraud_rate"], reverse=True)
    else:
        sorted_merchants = sorted(merchant_stats.values(), key=lambda x: x["total_amount"], reverse=True)

    return sorted_merchants[:limit]

@router.post("/generate")
async def generate_report(
    report: ReportGenerate,
    request: Request,
    token_data: TokenData = Depends(require_roles([UserRole.MANAGER, UserRole.ADMIN]))
):
    """Generate a comprehensive report."""
    supabase = request.app.state.supabase

    # Get data based on report type
    if report.report_type == "fraud_summary":
        data = await get_dashboard_metrics.__wrapped__.__wrapped__(request, 30, token_data)
    elif report.report_type == "model_comparison":
        data = await get_model_performance.__wrapped__(request)
    else:
        data = await get_timeseries_data.__wrapped__.__wrapped__(request, 30, "day", token_data)

    if report.format == "json":
        return data
    else:
        # Generate CSV
        output = io.StringIO()
        if isinstance(data, list) and data:
            fieldnames = data[0].keys()
            import csv
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)

        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={report.report_type}_{datetime.now().strftime('%Y%m%d')}.csv"}
        )

@router.get("/audit-log")
async def get_audit_log(
    request: Request,
    entity_type: Optional[str] = None,
    user_id: Optional[str] = None,
    action: Optional[str] = None,
    limit: int = Query(100, ge=1, le=1000),
    token_data: TokenData = Depends(require_roles([UserRole.ADMIN]))
):
    """Get audit log entries (Admin only)."""
    supabase = request.app.state.supabase

    query = supabase.table("audit_logs").select("*").order("created_at", desc=True).limit(limit)

    if entity_type:
        query = query.eq("entity_type", entity_type)
    if user_id:
        query = query.eq("user_id", user_id)
    if action:
        query = query.eq("action", action)

    result = query.execute()
    return result.data
