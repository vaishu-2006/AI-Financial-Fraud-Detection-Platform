"""
Real-time Fraud Scoring Engine

Provides sub-100ms scoring with:
- Feature extraction
- Model inference
- Anomaly detection
- Result caching
"""
import os
import pickle
import time
import numpy as np
from typing import Dict, Any, Optional
from datetime import datetime
import structlog

from ml.feature_engineering.extractor import FeatureExtractor, FeatureStore

logger = structlog.get_logger()


class FraudScorer:
    """Real-time fraud scoring engine."""

    def __init__(self, model_id: str, model_path: Optional[str] = None):
        self.model_id = model_id
        self.model_path = model_path
        self.model = None
        self.scaler = None
        self.anomaly_detector = None
        self.feature_extractor = FeatureExtractor()
        self.feature_store = FeatureStore()
        self.feature_names: list = []

        self._load_model()

    def _load_model(self):
        """Load model from disk."""
        if self.model_path and os.path.exists(self.model_path):
            with open(self.model_path, 'rb') as f:
                self.model = pickle.load(f)

            # Load scaler
            scaler_path = self.model_path.replace("model.pkl", "scaler.pkl")
            if os.path.exists(scaler_path):
                with open(scaler_path, 'rb') as f:
                    self.scaler = pickle.load(f)

            # Load anomaly detector
            anomaly_path = self.model_path.replace("model.pkl", "anomaly_detector.pkl")
            if os.path.exists(anomaly_path):
                with open(anomaly_path, 'rb') as f:
                    self.anomaly_detector = pickle.load(f)

            logger.info("Model loaded", model_id=self.model_id)

    def score(self, transaction: Dict[str, Any]) -> Dict[str, Any]:
        """
        Score a single transaction.

        Args:
            transaction: Transaction data dictionary

        Returns:
            Dict with risk_score, risk_label, confidence, and anomaly info
        """
        start_time = time.time()

        # Extract features
        features = self.feature_extractor.extract_features(transaction)
        feature_vector = self._prepare_features(features)

        # Get model prediction
        probability = self._predict_probability(feature_vector)

        # Convert to risk score (0-100)
        risk_score = self._probability_to_risk_score(probability)

        # Determine risk label
        risk_label = self._get_risk_label(risk_score)

        # Calculate confidence
        confidence = self._calculate_confidence(probability)

        # Anomaly detection
        anomaly_score, anomaly_detected = self._detect_anomaly(feature_vector)

        processing_time = (time.time() - start_time) * 1000

        logger.debug(
            "Transaction scored",
            transaction_id=transaction.get("transaction_id"),
            risk_score=risk_score,
            risk_label=risk_label,
            processing_time_ms=processing_time
        )

        return {
            "risk_score": risk_score,
            "risk_label": risk_label,
            "confidence": confidence,
            "anomaly_score": anomaly_score,
            "anomaly_detected": anomaly_detected,
            "processing_time_ms": processing_time,
            "model_id": self.model_id,
            "features_used": len(features)
        }

    def _prepare_features(self, features: Dict[str, float]) -> np.ndarray:
        """Prepare feature vector for model input."""
        # Ensure consistent feature ordering
        if not self.feature_names:
            self.feature_names = list(features.keys())

        feature_values = [features.get(name, 0) for name in self.feature_names]
        feature_vector = np.array(feature_values).reshape(1, -1)

        # Scale if scaler available
        if self.scaler:
            feature_vector = self.scaler.transform(feature_vector)

        return feature_vector

    def _predict_probability(self, features: np.ndarray) -> float:
        """Get fraud probability from model."""
        if self.model is None:
            return 0.5  # Default to neutral if no model

        if hasattr(self.model, 'predict_proba'):
            return self.model.predict_proba(features)[0, 1]
        else:
            return float(self.model.predict(features)[0])

    def _probability_to_risk_score(self, probability: float) -> float:
        """Convert probability (0-1) to risk score (0-100)."""
        # Apply calibration curve for better risk distribution
        # This helps spread out scores in the critical 20-80 range
        calibrated = probability ** 0.7  # Mild calibration
        return round(min(100, max(0, calibrated * 100)), 2)

    def _get_risk_label(self, risk_score: float) -> str:
        """Determine risk label from score."""
        if risk_score >= 70:
            return "fraudulent"
        elif risk_score >= 40:
            return "suspicious"
        else:
            return "safe"

    def _calculate_confidence(self, probability: float) -> float:
        """Calculate model confidence in the prediction."""
        # Confidence is higher when probability is further from 0.5
        return float(abs(probability - 0.5) * 2)

    def _detect_anomaly(self, features: np.ndarray) -> tuple:
        """Detect if transaction is anomalous."""
        if self.anomaly_detector is None:
            return 0.0, False

        try:
            # IsolationForest returns -1 for anomalies
            decision = self.anomaly_detector.decision_function(features)[0]
            # Convert to 0-1 score (higher = more anomalous)
            anomaly_score = max(0, min(1, (0.5 - decision)))

            # Threshold for anomaly detection
            is_anomaly = decision < -0.2

            return round(anomaly_score, 3), is_anomaly

        except Exception as e:
            logger.warning("Anomaly detection failed", error=str(e))
            return 0.0, False

    def score_batch(self, transactions: list) -> list:
        """Score multiple transactions."""
        return [self.score(tx) for tx in transactions]


class ScoringEngine:
    """High-level scoring engine with caching and background updates."""

    def __init__(self):
        self.active_scorer: Optional[FraudScorer] = None
        self._model_cache: Dict[str, FraudScorer] = {}

    def initialize(self, model_info: Dict[str, Any]):
        """Initialize with active model."""
        self.active_scorer = FraudScorer(
            model_id=model_info["id"],
            model_path=model_info.get("model_path")
        )

    def score(self, transaction: Dict[str, Any]) -> Dict[str, Any]:
        """Score a transaction using active model."""
        if self.active_scorer is None:
            raise RuntimeError("Scoring engine not initialized")

        return self.active_scorer.score(transaction)

    def health_check(self) -> Dict[str, Any]:
        """Check scoring engine health."""
        return {
            "initialized": self.active_scorer is not None,
            "model_id": self.active_scorer.model_id if self.active_scorer else None,
            "model_loaded": self.active_scorer.model is not None if self.active_scorer else False
        }
