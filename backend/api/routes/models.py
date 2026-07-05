"""
Model Management Routes - Training, Evaluation, Selection
"""
import os
import json
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from pydantic import BaseModel, Field
from enum import Enum
import structlog

from api.middleware.auth import TokenData, require_roles, UserRole

router = APIRouter()
logger = structlog.get_logger()

class ModelType(str, Enum):
    LOGISTIC_REGRESSION = "logistic_regression"
    RANDOM_FOREST = "random_forest"
    XGBOOST = "xgboost"
    LIGHTGBM = "lightgbm"
    NEURAL_NETWORK = "neural_network"
    ENSEMBLE = "ensemble"

class MetricType(str, Enum):
    F1_SCORE = "f1_score"
    ROC_AUC = "roc_auc"
    PRECISION = "precision"
    RECALL = "recall"
    PR_AUC = "pr_auc"

class TrainingConfig(BaseModel):
    model_name: str = "fraud_detector"
    model_types: List[ModelType] = [ModelType.XGBOOST, ModelType.LIGHTGBM]
    selection_metric: MetricType = MetricType.F1_SCORE

    # Data config
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    train_test_split: float = 0.8
    stratified_split: bool = True
    time_based_split: bool = True

    # Feature config
    feature_selection: bool = True
    n_features: Optional[int] = 50
    include_anomaly_features: bool = True

    # Hyperparameter tuning
    hyperparameter_tuning: bool = True
    n_trials: int = 50
    cv_folds: int = 5

    # Class imbalance handling
    sampling_strategy: str = "smote"  # smote, undersample, oversample, none
    use_class_weights: bool = True

    # Random seed for reproducibility
    random_seed: int = 42

class ModelSummary(BaseModel):
    id: str
    name: str
    version: str
    model_type: str
    status: str
    is_active: bool
    f1_score: Optional[float]
    precision_score: Optional[float]
    recall_score: Optional[float]
    roc_auc: Optional[float]
    trained_at: str

class TrainingResponse(BaseModel):
    job_id: str
    message: str
    config: TrainingConfig

class ModelDetail(ModelSummary):
    training_config: dict
    feature_columns: List[str]
    metrics: dict
    training_samples: Optional[int]
    fraud_rate: Optional[float]
    training_duration_seconds: Optional[int]
    deployed_at: Optional[str]
    deployed_by: Optional[str]

class ComparisonResponse(BaseModel):
    model_id: str
    model_type: str
    metric_values: Dict[str, float]
    confusion_matrix: List[List[int]]
    feature_importance_top10: List[Dict[str, Any]]

class DeploymentResponse(BaseModel):
    model_id: str
    previous_active: Optional[str]
    deployed_by: str
    deployed_at: str
    message: str

@router.post("/train", response_model=TrainingResponse)
async def start_training(
    config: TrainingConfig,
    background_tasks: BackgroundTasks,
    request: Request,
    token_data: TokenData = Depends(require_roles([UserRole.MANAGER, UserRole.ADMIN]))
):
    """
    Start a model training job.

    The training runs asynchronously. Use the job_id to track progress.
    Multiple model types can be trained and compared with automatic selection.
    """
    job_id = str(uuid.uuid4())
    supabase = request.app.state.supabase

    # Create pending model record
    for model_type in config.model_types:
        version = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        supabase.table("models").insert({
            "id": str(uuid.uuid4()),
            "user_id": token_data.user_id,
            "name": config.model_name,
            "version": f"{model_type.value}_{version}",
            "model_type": model_type.value,
            "training_config": config.model_dump(),
            "status": "training",
            "is_active": False
        }).execute()

    # Queue training task
    from ml.training.trainer import ModelTrainer
    trainer = ModelTrainer(config=config.model_dump(), job_id=job_id, user_id=token_data.user_id)
    background_tasks.add_task(trainer.train)

    return TrainingResponse(
        job_id=job_id,
        message=f"Training started for {len(config.model_types)} model types",
        config=config
    )

@router.get("", response_model=List[ModelSummary])
async def list_models(
    request: Request,
    status: Optional[str] = None,
    model_type: Optional[str] = None,
    limit: int = 20,
    token_data: TokenData = Depends(require_roles([UserRole.ANALYST, UserRole.MANAGER, UserRole.ADMIN]))
):
    """List trained models with optional filters."""
    supabase = request.app.state.supabase

    query = supabase.table("models").select("*").order("trained_at", desc=True).limit(limit)

    if status:
        query = query.eq("status", status)
    if model_type:
        query = query.eq("model_type", model_type)

    result = query.execute()
    return result.data

@router.get("/active", response_model=ModelDetail)
async def get_active_model(request: Request):
    """Get the currently deployed active model."""
    supabase = request.app.state.supabase

    result = supabase.table("models").select("*").eq("is_active", True).maybe_single().execute()

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active model deployed"
        )

    return result.data

@router.get("/{model_id}", response_model=ModelDetail)
async def get_model(
    model_id: str,
    request: Request,
    token_data: TokenData = Depends(require_roles([UserRole.ANALYST, UserRole.MANAGER, UserRole.ADMIN]))
):
    """Get detailed information about a specific model."""
    supabase = request.app.state.supabase

    result = supabase.table("models").select("*").eq("id", model_id).maybe_single().execute()

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found"
        )

    return result.data

@router.post("/{model_id}/deploy", response_model=DeploymentResponse)
async def deploy_model(
    model_id: str,
    request: Request,
    token_data: TokenData = Depends(require_roles([UserRole.MANAGER, UserRole.ADMIN]))
):
    """
    Deploy a model as the active scoring model.

    Only one model can be active at a time. Deploying a new model
    will deactivate the previously active model.
    """
    supabase = request.app.state.supabase

    # Check model exists and is ready
    model = supabase.table("models").select("*").eq("id", model_id).maybe_single().execute()
    if not model.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found"
        )

    if model.data["status"] != "validating" and model.data["status"] != "training":
        # Allow deploying completed models
        pass

    # Get current active model
    current_active = supabase.table("models").select("id").eq("is_active", True).maybe_single().execute()
    previous_id = current_active.data.get("id") if current_active.data else None

    # Deactivate previous model
    if previous_id:
        supabase.table("models").update({
            "is_active": False,
            "status": "deprecated"
        }).eq("id", previous_id).execute()

    # Activate new model
    deploy_time = datetime.utcnow()
    supabase.table("models").update({
        "is_active": True,
        "status": "deployed",
        "deployed_at": deploy_time.isoformat(),
        "deployed_by": token_data.user_id
    }).eq("id", model_id).execute()

    return DeploymentResponse(
        model_id=model_id,
        previous_active=previous_id,
        deployed_by=token_data.user_id,
        deployed_at=deploy_time.isoformat(),
        message="Model deployed successfully"
    )

@router.post("/{model_id}/deprecate")
async def deprecate_model(
    model_id: str,
    request: Request,
    token_data: TokenData = Depends(require_roles([UserRole.ADMIN]))
):
    """Mark a model as deprecated (Admin only)."""
    supabase = request.app.state.supabase

    result = supabase.table("models").update({
        "status": "deprecated",
        "is_active": False
    }).eq("id", model_id).execute()

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found"
        )

    return {"message": "Model deprecated", "model_id": model_id}

@router.get("/{model_id}/compare", response_model=ComparisonResponse)
async def compare_model(
    model_id: str,
    request: Request,
    baseline_id: Optional[str] = None,
    token_data: TokenData = Depends(require_roles([UserRole.ANALYST, UserRole.MANAGER, UserRole.ADMIN]))
):
    """Compare model performance metrics and feature importance."""
    supabase = request.app.state.supabase

    model = supabase.table("models").select("*").eq("id", model_id).maybe_single().execute()
    if not model.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found"
        )

    metrics = model.data.get("metrics", {})

    return ComparisonResponse(
        model_id=model_id,
        model_type=model.data["model_type"],
        metric_values={
            "f1_score": model.data.get("f1_score", 0),
            "precision": model.data.get("precision_score", 0),
            "recall": model.data.get("recall_score", 0),
            "roc_auc": model.data.get("roc_auc", 0),
            "pr_auc": model.data.get("pr_auc", 0)
        },
        confusion_matrix=metrics.get("confusion_matrix", [[0, 0], [0, 0]]),
        feature_importance_top10=metrics.get("feature_importance_top10", [])
    )

@router.post("/compare-all")
async def compare_all_models(
    request: Request,
    token_data: TokenData = Depends(require_roles([UserRole.ANALYST, UserRole.MANAGER, UserRole.ADMIN]))
):
    """Compare all trained models side-by-side."""
    supabase = request.app.state.supabase

    result = supabase.table("models").select("id, name, version, model_type, f1_score, precision_score, recall_score, roc_auc, trained_at, status").neq("status", "training").execute()

    comparison = {
        "models": result.data,
        "best_by_metric": {
            "f1": max(result.data, key=lambda x: x.get("f1_score") or 0) if result.data else None,
            "roc_auc": max(result.data, key=lambda x: x.get("roc_auc") or 0) if result.data else None,
            "precision": max(result.data, key=lambda x: x.get("precision_score") or 0) if result.data else None,
            "recall": max(result.data, key=lambda x: x.get("recall_score") or 0) if result.data else None
        }
    }

    return comparison

@router.delete("/{model_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_model(
    model_id: str,
    request: Request,
    token_data: TokenData = Depends(require_roles([UserRole.ADMIN]))
):
    """Delete a model (Admin only). Cannot delete active model."""
    supabase = request.app.state.supabase

    # Check if active
    model = supabase.table("models").select("is_active").eq("id", model_id).maybe_single().execute()

    if model.data and model.data.get("is_active"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete active model. Deploy another model first."
        )

    supabase.table("models").delete().eq("id", model_id).execute()
