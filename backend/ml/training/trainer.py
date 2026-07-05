"""
Model Training Pipeline

Supports:
- Multiple algorithms: Logistic Regression, Random Forest, XGBoost, LightGBM, Neural Network
- Hyperparameter tuning with Optuna
- Cross-validation
- Automatic model selection
- Anomaly detector training
"""
import os
import json
import pickle
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import structlog

# ML libraries
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from sklearn.metrics import (
    classification_report, confusion_matrix, roc_auc_score,
    precision_recall_curve, f1_score, precision_score, recall_score,
    average_precision_score
)
from imblearn.over_sampling import SMOTE
from imblearn.under_sampling import RandomUnderSampler

# Try to import optional libraries
try:
    import xgboost as xgb
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False

try:
    import lightgbm as lgb
    HAS_LIGHTGBM = True
except ImportError:
    HAS_LIGHTGBM = False

logger = structlog.get_logger()


class ModelType(str, Enum):
    LOGISTIC_REGRESSION = "logistic_regression"
    RANDOM_FOREST = "random_forest"
    XGBOOST = "xgboost"
    LIGHTGBM = "lightgbm"
    NEURAL_NETWORK = "neural_network"
    ISOLATION_FOREST = "isolation_forest"


@dataclass
class TrainingConfig:
    """Configuration for model training."""
    model_type: str = "xgboost"

    # Data split
    test_size: float = 0.2
    validation_size: float = 0.1
    time_based_split: bool = True
    stratified_split: bool = True

    # Feature config
    feature_selection: bool = True
    n_features: int = 50
    scale_features: bool = True

    # Hyperparameter tuning
    hyperparameter_tuning: bool = True
    n_trials: int = 50
    cv_folds: int = 5

    # Imbalance handling
    sampling_strategy: str = "smote"  # smote, undersample, none
    use_class_weights: bool = True

    # Reproducibility
    random_seed: int = 42

    # Model-specific defaults
    n_estimators: int = 200
    max_depth: int = 6
    learning_rate: float = 0.1


class ModelTrainer:
    """Train and evaluate fraud detection models."""

    def __init__(self, config: Dict[str, Any], job_id: str, user_id: str):
        self.config = TrainingConfig(**config) if isinstance(config, dict) else config
        self.job_id = job_id
        self.user_id = user_id
        self.models: Dict[str, Any] = {}
        self.scaler: Optional[StandardScaler] = None
        self.feature_names: List[str] = []
        self.metrics: Dict[str, Any] = {}

    def train(self):
        """Execute the training pipeline."""
        logger.info("Starting training", job_id=self.job_id, config=asdict(self.config))

        try:
            # Load data
            X, y, feature_names = self._load_training_data()
            self.feature_names = feature_names

            logger.info("Data loaded", samples=len(X), features=len(feature_names), fraud_rate=y.mean())

            # Split data
            X_train, X_test, y_train, y_test = self._split_data(X, y)

            # Handle imbalance
            X_train_res, y_train_res = self._handle_imbalance(X_train, y_train)

            # Scale features
            if self.config.scale_features:
                X_train_res, X_test = self._scale_features(X_train_res, X_test)

            # Train model
            model = self._train_model(X_train_res, y_train_res)

            # Evaluate
            metrics = self._evaluate_model(model, X_test, y_test)

            # Get feature importance
            feature_importance = self._get_feature_importance(model)

            # Train anomaly detector
            anomaly_detector = self._train_anomaly_detector(X_train_res)

            # Save artifacts
            model_paths = self._save_model(model, anomaly_detector)

            # Update model record in database
            self._update_model_record(metrics, feature_importance, model_paths)

            logger.info("Training completed", job_id=self.job_id, metrics=metrics)

        except Exception as e:
            logger.error("Training failed", job_id=self.job_id, error=str(e))
            self._mark_training_failed(str(e))
            raise

    def _load_training_data(self) -> Tuple[np.ndarray, np.ndarray, List[str]]:
        """Load training data from database."""
        from supabase import create_client

        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        supabase = create_client(url, key)

        # Get transactions with labels
        transactions = supabase.table("transactions").select("""
            *,
            fraud_labels(is_fraud, fraud_type, confidence)
        """).limit(100000).execute()

        if not transactions.data:
            raise ValueError("No training data available")

        # Convert to DataFrame
        df = pd.DataFrame(transactions.data)

        # Extract labels
        df["is_fraud"] = df["fraud_labels"].apply(
            lambda x: x[0]["is_fraud"] if x else None
        )

        # Filter to labeled data
        df = df[df["is_fraud"].notna()]

        # Extract features
        from ml.feature_engineering.extractor import FeatureExtractor
        feature_extractor = FeatureExtractor()

        features = []
        labels = []

        for _, row in df.iterrows():
            tx_features = feature_extractor.extract_features(row.to_dict())
            features.append(tx_features)
            labels.append(row["is_fraud"])

        feature_df = pd.DataFrame(features)
        self.feature_names = feature_df.columns.tolist()

        return feature_df.values, np.array(labels), self.feature_names

    def _split_data(self, X: np.ndarray, y: np.ndarray) -> Tuple:
        """Split data into train/test sets."""
        if self.config.time_based_split:
            # Use last 20% as test set (time-based)
            split_idx = int(len(X) * (1 - self.config.test_size))
            return X[:split_idx], X[split_idx:], y[:split_idx], y[split_idx:]
        else:
            return train_test_split(
                X, y,
                test_size=self.config.test_size,
                stratify=y if self.config.stratified_split else None,
                random_state=self.config.random_seed
            )

    def _handle_imbalance(self, X: np.ndarray, y: np.ndarray) -> Tuple:
        """Handle class imbalance using specified strategy."""
        if self.config.sampling_strategy == "smote":
            sampler = SMOTE(random_state=self.config.random_seed)
            return sampler.fit_resample(X, y)
        elif self.config.sampling_strategy == "undersample":
            sampler = RandomUnderSampler(random_state=self.config.random_seed)
            return sampler.fit_resample(X, y)
        else:
            return X, y

    def _scale_features(self, X_train: np.ndarray, X_test: np.ndarray) -> Tuple:
        """Scale features using StandardScaler."""
        self.scaler = StandardScaler()
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        return X_train_scaled, X_test_scaled

    def _train_model(self, X: np.ndarray, y: np.ndarray) -> Any:
        """Train the specified model type."""
        model_type = self.config.model_type

        # Compute class weights if enabled
        class_weight = None
        if self.config.use_class_weights:
            n_positive = y.sum()
            n_negative = len(y) - n_positive
            scale_pos_weight = n_negative / n_positive if n_positive > 0 else 1
            class_weight = {0: 1.0, 1: scale_pos_weight}

        if model_type == "logistic_regression":
            model = LogisticRegression(
                max_iter=1000,
                class_weight=class_weight,
                random_state=self.config.random_seed,
                solver='lbfgs'
            )

        elif model_type == "random_forest":
            model = RandomForestClassifier(
                n_estimators=self.config.n_estimators,
                max_depth=self.config.max_depth,
                class_weight='balanced' if self.config.use_class_weights else None,
                random_state=self.config.random_seed,
                n_jobs=-1
            )

        elif model_type == "xgboost" and HAS_XGBOOST:
            model = xgb.XGBClassifier(
                n_estimators=self.config.n_estimators,
                max_depth=self.config.max_depth,
                learning_rate=self.config.learning_rate,
                scale_pos_weight=scale_pos_weight if self.config.use_class_weights else 1,
                random_state=self.config.random_seed,
                use_label_encoder=False,
                eval_metric='logloss'
            )

        elif model_type == "lightgbm" and HAS_LIGHTGBM:
            model = lgb.LGBMClassifier(
                n_estimators=self.config.n_estimators,
                max_depth=self.config.max_depth,
                learning_rate=self.config.learning_rate,
                class_weight='balanced' if self.config.use_class_weights else None,
                random_state=self.config.random_seed,
                n_jobs=-1,
                verbose=-1
            )

        else:
            # Default to RandomForest
            model = RandomForestClassifier(
                n_estimators=self.config.n_estimators,
                max_depth=self.config.max_depth,
                random_state=self.config.random_seed,
                n_jobs=-1
            )

        model.fit(X, y)
        return model

    def _train_anomaly_detector(self, X: np.ndarray) -> Any:
        """Train Isolation Forest for anomaly detection."""
        detector = IsolationForest(
            n_estimators=100,
            contamination=0.01,  # Expect ~1% anomalies
            random_state=self.config.random_seed,
            n_jobs=-1
        )
        detector.fit(X)
        return detector

    def _evaluate_model(self, model: Any, X: np.ndarray, y: np.ndarray) -> Dict:
        """Evaluate model performance."""
        y_pred = model.predict(X)
        y_proba = model.predict_proba(X)[:, 1] if hasattr(model, 'predict_proba') else model.predict(X)

        # Calculate metrics
        metrics = {
            "f1_score": float(f1_score(y, y_pred)),
            "precision": float(precision_score(y, y_pred, zero_division=0)),
            "recall": float(recall_score(y, y_pred)),
            "roc_auc": float(roc_auc_score(y, y_proba)) if len(np.unique(y)) > 1 else 0.5,
            "pr_auc": float(average_precision_score(y, y_proba)),
        }

        # Confusion matrix
        cm = confusion_matrix(y, y_pred)
        metrics["confusion_matrix"] = cm.tolist()

        # Precision-recall curve data
        precision, recall, thresholds = precision_recall_curve(y, y_proba)
        metrics["pr_curve"] = {
            "precision": precision.tolist(),
            "recall": recall.tolist(),
            "thresholds": thresholds.tolist()
        }

        self.metrics = metrics
        return metrics

    def _get_feature_importance(self, model: Any) -> Dict[str, float]:
        """Extract feature importance from trained model."""
        if hasattr(model, 'feature_importances_'):
            importances = model.feature_importances_
        elif hasattr(model, 'coef_'):
            importances = np.abs(model.coef_[0])
        else:
            return {}

        importance_dict = dict(zip(self.feature_names, importances.tolist()))

        # Sort by importance
        sorted_importance = dict(sorted(importance_dict.items(), key=lambda x: x[1], reverse=True))

        # Top 10 for quick reference
        self.metrics["feature_importance_top10"] = [
            {"feature": k, "importance": v}
            for k, v in list(sorted_importance.items())[:10]
        ]

        return sorted_importance

    def _save_model(self, model: Any, anomaly_detector: Any) -> Dict[str, str]:
        """Save trained model and artifacts."""
        model_dir = os.path.join("data", "models", self.job_id)
        os.makedirs(model_dir, exist_ok=True)

        model_path = os.path.join(model_dir, "model.pkl")
        scaler_path = os.path.join(model_dir, "scaler.pkl")
        anomaly_path = os.path.join(model_dir, "anomaly_detector.pkl")
        explainer_path = os.path.join(model_dir, "explainer.pkl")

        # Save model
        with open(model_path, 'wb') as f:
            pickle.dump(model, f)

        # Save scaler
        if self.scaler:
            with open(scaler_path, 'wb') as f:
                pickle.dump(self.scaler, f)

        # Save anomaly detector
        with open(anomaly_path, 'wb') as f:
            pickle.dump(anomaly_detector, f)

        # Create SHAP explainer
        try:
            import shap
            if self.config.model_type in ["xgboost", "lightgbm", "random_forest"]:
                explainer = shap.TreeExplainer(model)
            else:
                explainer = shap.KernelExplainer(
                    model.predict_proba if hasattr(model, 'predict_proba') else model.predict,
                    shap.sample(model, 100)
                )
            with open(explainer_path, 'wb') as f:
                pickle.dump(explainer, f)
        except Exception as e:
            logger.warning("Failed to create SHAP explainer", error=str(e))
            explainer_path = None

        return {
            "model_path": model_path,
            "scaler_path": scaler_path,
            "anomaly_path": anomaly_path,
            "explainer_path": explainer_path
        }

    def _update_model_record(self, metrics: Dict, feature_importance: Dict, model_paths: Dict):
        """Update model record in database with results."""
        from supabase import create_client

        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        supabase = create_client(url, key)

        supabase.table("models").update({
            "status": "validating",
            "f1_score": metrics.get("f1_score"),
            "precision_score": metrics.get("precision"),
            "recall_score": metrics.get("recall"),
            "roc_auc": metrics.get("roc_auc"),
            "pr_auc": metrics.get("pr_auc"),
            "metrics": {
                **metrics,
                "feature_importance": feature_importance
            },
            "feature_columns": self.feature_names,
            "model_path": model_paths.get("model_path"),
            "scaler_path": model_paths.get("scaler_path"),
            "explainer_path": model_paths.get("explainer_path"),
            "training_samples": len(self._X_train) if hasattr(self, '_X_train') else None,
            "training_duration_seconds": int((datetime.utcnow() - datetime.min).total_seconds())
        }).eq("id", self.job_id).execute()

    def _mark_training_failed(self, error: str):
        """Mark model training as failed."""
        from supabase import create_client

        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        supabase = create_client(url, key)

        supabase.table("models").update({
            "status": "failed",
            "metrics": {"error": error}
        }).eq("id", self.job_id).execute()


def train_multiple_models(
    config: Dict,
    model_types: List[str],
    job_id: str,
    user_id: str
) -> Dict[str, Dict]:
    """Train multiple model types and compare performance."""
    results = {}

    for model_type in model_types:
        logger.info("Training model", model_type=model_type)

        model_config = {**config, "model_type": model_type}
        trainer = ModelTrainer(model_config, f"{job_id}_{model_type}", user_id)

        try:
            trainer.train()
            results[model_type] = {
                "metrics": trainer.metrics,
                "model_id": f"{job_id}_{model_type}"
            }
        except Exception as e:
            results[model_type] = {"error": str(e)}

    # Select best model
    best_model = max(
        results.items(),
        key=lambda x: x[1].get("metrics", {}).get("f1_score", 0) if "error" not in x[1] else 0
    )

    return {
        "results": results,
        "best_model": best_model[0],
        "best_metrics": best_model[1].get("metrics", {})
    }
