"""
Real-time Fraud Scoring Routes
"""
import os
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from pydantic import BaseModel, Field
from decimal import Decimal
import structlog

from api.middleware.auth import TokenData, require_roles, UserRole
from ml.inference.scorer import FraudScorer
from ml.explainability.shap_explainer import ShapExplainer

router = APIRouter()
logger = structlog.get_logger()

class ScoringRequest(BaseModel):
    transaction_id: str
    customer_id: str
    merchant_id: str
    amount: Decimal
    currency: str = "USD"
    transaction_type: str = "purchase"
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    country: Optional[str] = None
    city: Optional[str] = None
    ip_address: Optional[str] = None
    device_id: Optional[str] = None
    device_type: Optional[str] = None
    channel: str = "web"
    transaction_timestamp: datetime
    customer_age_days: Optional[int] = None
    merchant_category: Optional[str] = None

class BatchScoringRequest(BaseModel):
    transactions: List[ScoringRequest]
    callback_url: Optional[str] = None

class ShapExplanationResponse(BaseModel):
    base_value: float
    feature_contributions: List[Dict[str, Any]]
    output_value: float
    top_factors: List[Dict[str, Any]]

class ScoringResponse(BaseModel):
    transaction_id: str
    risk_score: float = Field(..., ge=0, le=100)
    risk_label: str = Field(..., pattern="^(safe|suspicious|fraudulent)$")
    confidence: float = Field(..., ge=0, le=1)
    model_id: str
    model_type: str
    explanation: ShapExplanationResponse
    anomaly_score: Optional[float] = None
    anomaly_detected: bool = False
    processing_time_ms: float

class BatchScoringResponse(BaseModel):
    total: int
    processed: int
    job_id: str
    status: str

@router.post("/single", response_model=ScoringResponse)
async def score_single_transaction(
    scoring_request: ScoringRequest,
    request: Request,
    token_data: TokenData = Depends(require_roles([UserRole.ANALYST, UserRole.MANAGER, UserRole.ADMIN]))
):
    """
    Score a single transaction in real-time.

    Returns:
    - **risk_score**: 0-100 risk score
    - **risk_label**: safe, suspicious, or fraudulent
    - **confidence**: Model confidence in the prediction
    - **explanation**: SHAP values explaining the score
    - **anomaly_score**: Optional anomaly detection score

    Target latency: <100ms
    """
    import time
    start_time = time.time()

    supabase = request.app.state.supabase

    # Get active model
    active_model = supabase.table("models").select("*").eq("is_active", True).maybe_single().execute()

    if not active_model.data:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No active model deployed. Please train and deploy a model first."
        )

    model_info = active_model.data

    # Initialize scorer
    scorer = FraudScorer(model_id=model_info["id"], model_path=model_info.get("model_path"))

    try:
        # Score the transaction
        result = scorer.score(scoring_request.model_dump())

        # Get SHAP explanation
        explainer = ShapExplainer(
            model_id=model_info["id"],
            explainer_path=model_info.get("explainer_path")
        )
        explanation = explainer.explain(scoring_request.model_dump(), result["risk_score"])

        # Update transaction in database
        supabase.table("transactions").update({
            "risk_score": result["risk_score"],
            "risk_label": result["risk_label"],
            "model_id": model_info["id"]
        }).eq("transaction_id", scoring_request.transaction_id).execute()

        processing_time = (time.time() - start_time) * 1000

        return ScoringResponse(
            transaction_id=scoring_request.transaction_id,
            risk_score=result["risk_score"],
            risk_label=result["risk_label"],
            confidence=result["confidence"],
            model_id=model_info["id"],
            model_type=model_info["model_type"],
            explanation=explanation,
            anomaly_score=result.get("anomaly_score"),
            anomaly_detected=result.get("anomaly_detected", False),
            processing_time_ms=processing_time
        )

    except Exception as e:
        logger.error("Scoring failed", error=str(e), transaction_id=scoring_request.transaction_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Scoring failed: {str(e)}"
        )

@router.post("/batch", response_model=BatchScoringResponse)
async def score_batch_transactions(
    batch_request: BatchScoringRequest,
    background_tasks: BackgroundTasks,
    request: Request,
    token_data: TokenData = Depends(require_roles([UserRole.MANAGER, UserRole.ADMIN]))
):
    """
    Submit a batch of transactions for scoring.

    Processing happens asynchronously. Returns a job ID to track progress.
    Use the callback_url to receive results when processing completes.
    """
    import uuid
    supabase = request.app.state.supabase

    job_id = str(uuid.uuid4())

    # Create job record
    supabase.table("batch_jobs").insert({
        "id": job_id,
        "user_id": token_data.user_id,
        "type": "batch_scoring",
        "status": "pending",
        "total": len(batch_request.transactions),
        "processed": 0,
        "callback_url": batch_request.callback_url
    }).execute()

    # Queue background processing
    background_tasks.add_task(
        process_batch_scoring,
        job_id,
        batch_request.transactions,
        token_data.user_id
    )

    return BatchScoringResponse(
        total=len(batch_request.transactions),
        processed=0,
        job_id=job_id,
        status="pending"
    )

@router.get("/job/{job_id}")
async def get_scoring_job_status(
    job_id: str,
    request: Request,
    token_data: TokenData = Depends(require_roles([UserRole.ANALYST, UserRole.MANAGER, UserRole.ADMIN]))
):
    """Get status of a batch scoring job."""
    supabase = request.app.state.supabase

    result = supabase.table("batch_jobs").select("*").eq("id", job_id).maybe_single().execute()

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )

    return result.data

@router.get("/explain/{transaction_id}", response_model=ShapExplanationResponse)
async def get_explanation(
    transaction_id: str,
    request: Request,
    token_data: TokenData = Depends(require_roles([UserRole.ANALYST, UserRole.MANAGER, UserRole.ADMIN]))
):
    """
    Get SHAP explanation for a previously scored transaction.

    Returns detailed feature contributions showing why the model made its decision.
    """
    supabase = request.app.state.supabase

    # Get transaction
    transaction = supabase.table("transactions").select("*").eq("id", transaction_id).maybe_single().execute()
    if not transaction.data:
        transaction = supabase.table("transactions").select("*").eq("transaction_id", transaction_id).maybe_single().execute()

    if not transaction.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )

    if not transaction.data.get("model_id"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Transaction has not been scored yet"
        )

    # Get model info
    model = supabase.table("models").select("*").eq("id", transaction.data["model_id"]).maybe_single().execute()

    if not model.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found"
        )

    # Generate explanation
    explainer = ShapExplainer(
        model_id=model.data["id"],
        explainer_path=model.data.get("explainer_path")
    )

    explanation = explainer.explain(
        transaction.data,
        transaction.data.get("risk_score", 0)
    )

    return explanation

@router.get("/feature-importance/{model_id}")
async def get_feature_importance(
    model_id: str,
    request: Request,
    token_data: TokenData = Depends(require_roles([UserRole.ANALYST, UserRole.MANAGER, UserRole.ADMIN]))
):
    """Get global feature importance for a model."""
    supabase = request.app.state.supabase

    model = supabase.table("models").select("*").eq("id", model_id).maybe_single().execute()

    if not model.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found"
        )

    # Get feature importance from model metrics
    metrics = model.data.get("metrics", {})
    feature_importance = metrics.get("feature_importance", {})

    if not feature_importance:
        # Compute on the fly
        explainer = ShapExplainer(model_id=model_id, explainer_path=model.data.get("explainer_path"))
        feature_importance = explainer.get_global_importance()

    return {
        "model_id": model_id,
        "model_type": model.data["model_type"],
        "feature_importance": feature_importance
    }

async def process_batch_scoring(job_id: str, transactions: List[dict], user_id: str):
    """Background task to process batch scoring."""
    supabase = get_supabase_client()

    try:
        # Get active model
        active_model = supabase.table("models").select("*").eq("is_active", True).maybe_single().execute()
        if not active_model.data:
            supabase.table("batch_jobs").update({"status": "failed", "error": "No active model"}).eq("id", job_id).execute()
            return

        model_info = active_model.data
        scorer = FraudScorer(model_id=model_info["id"], model_path=model_info.get("model_path"))

        processed = 0
        for tx in transactions:
            try:
                result = scorer.score(tx)

                # Update transaction
                supabase.table("transactions").update({
                    "risk_score": result["risk_score"],
                    "risk_label": result["risk_label"],
                    "model_id": model_info["id"]
                }).eq("transaction_id", tx["transaction_id"]).execute()

                processed += 1

                # Update job progress
                supabase.table("batch_jobs").update({"processed": processed}).eq("id", job_id).execute()

            except Exception as e:
                logger.error("Failed to score transaction", transaction_id=tx.get("transaction_id"), error=str(e))

        # Mark job complete
        supabase.table("batch_jobs").update({
            "status": "completed",
            "processed": processed,
            "completed_at": datetime.utcnow().isoformat()
        }).eq("id", job_id).execute()

    except Exception as e:
        logger.error("Batch scoring job failed", job_id=job_id, error=str(e))
        supabase.table("batch_jobs").update({
            "status": "failed",
            "error": str(e)
        }).eq("id", job_id).execute()

def get_supabase_client():
    """Helper to get supabase client for background tasks."""
    from supabase import create_client
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    return create_client(url, key)
