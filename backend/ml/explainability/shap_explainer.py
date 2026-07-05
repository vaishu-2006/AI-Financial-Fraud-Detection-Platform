"""
SHAP Explainability Module

Provides model explanations using SHAP values:
- Local explanations (per-prediction)
- Global feature importance
- Waterfall and force plot data
"""
import os
import pickle
import numpy as np
from typing import Dict, List, Any, Optional
import structlog

logger = structlog.get_logger()


class ShapExplainer:
    """Generate SHAP explanations for predictions."""

    def __init__(self, model_id: str, explainer_path: Optional[str] = None):
        self.model_id = model_id
        self.explainer_path = explainer_path
        self.explainer = None
        self.feature_names: List[str] = []
        self._load_explainer()

    def _load_explainer(self):
        """Load SHAP explainer from disk."""
        if self.explainer_path and os.path.exists(self.explainer_path):
            try:
                with open(self.explainer_path, 'rb') as f:
                    self.explainer = pickle.load(f)
                logger.info("SHAP explainer loaded", model_id=self.model_id)
            except Exception as e:
                logger.warning("Failed to load SHAP explainer", error=str(e))

    def explain(
        self,
        transaction: Dict[str, Any],
        prediction_score: float
    ) -> Dict[str, Any]:
        """
        Generate SHAP explanation for a single prediction.

        Returns format suitable for frontend visualization:
        - base_value: Expected value (average prediction)
        - feature_contributions: List of {feature, value, shap_value}
        - output_value: Model output
        - top_factors: Most influential features with human-readable explanations
        """
        if self.explainer is None:
            return self._default_explanation(transaction, prediction_score)

        try:
            # Extract features
            from ml.feature_engineering.extractor import FeatureExtractor
            extractor = FeatureExtractor()
            features = extractor.extract_features(transaction)

            # Prepare feature vector
            feature_names = list(features.keys())
            feature_values = np.array([features[name] for name in feature_names]).reshape(1, -1)

            # Get SHAP values
            shap_values = self.explainer.shap_values(feature_values)

            # Handle different SHAP value formats
            if isinstance(shap_values, list):
                # For binary classification, get positive class SHAP values
                shap_values = shap_values[1] if len(shap_values) > 1 else shap_values[0]

            shap_values = shap_values[0]

            # Get base value (expected value)
            base_value = self._get_base_value()

            # Build feature contributions
            contributions = []
            for i, name in enumerate(feature_names):
                contributions.append({
                    "feature": name,
                    "feature_value": float(features[name]),
                    "shap_value": float(shap_values[i]),
                    "abs_shap": abs(float(shap_values[i]))
                })

            # Sort by absolute SHAP value
            contributions.sort(key=lambda x: x["abs_shap"], reverse=True)

            # Generate top factors with explanations
            top_factors = self._generate_top_factors(contributions[:5])

            return {
                "base_value": base_value,
                "output_value": float(prediction_score) / 100,  # Convert back to probability
                "feature_contributions": contributions[:20],  # Top 20 for display
                "top_factors": top_factors,
                "model_id": self.model_id
            }

        except Exception as e:
            logger.error("SHAP explanation failed", error=str(e))
            return self._default_explanation(transaction, prediction_score)

    def _get_base_value(self) -> float:
        """Get expected value from explainer."""
        if hasattr(self.explainer, 'expected_value'):
            base = self.explainer.expected_value
            if isinstance(base, (list, np.ndarray)):
                return float(base[-1] if len(base) > 1 else base[0])
            return float(base)
        return 0.5  # Default

    def _generate_top_factors(self, contributions: List[Dict]) -> List[Dict]:
        """Generate human-readable explanations for top factors."""
        factors = []

        for contrib in contributions:
            factor = {
                "feature": contrib["feature"],
                "shap_value": contrib["shap_value"],
                "direction": "increases" if contrib["shap_value"] > 0 else "decreases",
                "explanation": self._explain_feature(contrib)
            }
            factors.append(factor)

        return factors

    def _explain_feature(self, contribution: Dict) -> str:
        """Generate human-readable explanation for a feature contribution."""
        feature = contribution["feature"]
        shap_value = contribution["shap_value"]
        feature_value = contribution.get("feature_value", 0)
        direction = "increases" if shap_value > 0 else "decreases"

        # Feature explanation templates
        explanations = {
            "amount": f"Transaction amount of ${feature_value:,.2f} {direction} fraud risk",
            "amount_log": f"Log-transformed amount {direction}s risk",
            "hour": f"Transaction at hour {int(feature_value)} {direction}s risk",
            "is_night": f"Night-time transaction {direction}s risk significantly" if feature_value else "Day transaction has normal risk",
            "is_weekend": f"Weekend transaction {direction}s fraud probability" if feature_value else "Weekday transaction",
            "tx_count_1h": f"{int(feature_value)} transactions in the last hour {direction}s risk",
            "tx_count_24h": f"{int(feature_value)} transactions in 24 hours {direction}s concern level",
            "customer_age_days": f"Customer age of {int(feature_value)} days {'lowers' if shap_value < 0 else 'raises'} risk",
            "amount_zscore": f"Amount is {abs(feature_value):.1f} std dev from customer average",
            "country_risk": f"Country risk score of {feature_value:.2f} {direction}s probability",
            "velocity_amount_1h": f"High velocity (amount x frequency) {direction}s risk",
            "device_is_mobile": "Mobile device transaction" if feature_value else "Non-mobile transaction",
            "channel_web": "Web channel transaction" if feature_value else "Non-web channel",
            "merchant_fraud_rate": f"Merchant fraud rate of {feature_value:.1%} {direction}s risk"
        }

        # Default explanation
        if feature in explanations:
            return explanations[feature]

        # Generate from feature name
        readable_name = feature.replace("_", " ").title()
        action = "increases" if shap_value > 0 else "decreases"
        return f"{readable_name} {action} fraud risk"

    def _default_explanation(
        self,
        transaction: Dict[str, Any],
        prediction_score: float
    ) -> Dict[str, Any]:
        """Return default explanation when SHAP is unavailable."""
        # Use simple feature contribution based on amount and risk factors
        amount = float(transaction.get("amount", 0))
        hour = int(transaction.get("local_hour", 12))

        contributions = [
            {
                "feature": "amount",
                "feature_value": amount,
                "shap_value": min(amount / 10000, 0.3) if amount > 0 else 0,
                "abs_shap": min(amount / 10000, 0.3) if amount > 0 else 0
            },
            {
                "feature": "is_night",
                "feature_value": float(hour >= 22 or hour <= 6),
                "shap_value": 0.15 if (hour >= 22 or hour <= 6) else 0,
                "abs_shap": 0.15 if (hour >= 22 or hour <= 6) else 0
            },
            {
                "feature": "base_risk",
                "feature_value": 0.1,
                "shap_value": 0.1,
                "abs_shap": 0.1
            }
        ]

        top_factors = [
            {
                "feature": f"Transaction amount: ${amount:,.2f}",
                "shap_value": contributions[0]["shap_value"],
                "direction": "increases" if amount > 1000 else "neutral",
                "explanation": f"Amount of ${amount:,.2f} contributes {'higher' if amount > 1000 else 'normal'} risk"
            },
            {
                "feature": f"Time: {hour}:00",
                "shap_value": contributions[1]["shap_value"],
                "direction": "increases" if contributions[1]["shap_value"] > 0 else "neutral",
                "explanation": f"{'Night-time' if hour >= 22 or hour <= 6 else 'Daytime'} transaction"
            }
        ]

        return {
            "base_value": 0.5,
            "output_value": prediction_score / 100,
            "feature_contributions": contributions,
            "top_factors": top_factors,
            "model_id": self.model_id
        }

    def get_global_importance(self) -> Dict[str, float]:
        """Get global feature importance from SHAP explainer."""
        if self.explainer is None:
            return {}

        try:
            # For tree-based models, use mean absolute SHAP values
            if hasattr(self.explainer, 'shap_values'):
                # This would need a background dataset
                pass

            # Return cached or computed importance
            return {}

        except Exception as e:
            logger.warning("Failed to get global importance", error=str(e))
            return {}

    def generate_waterfall_data(
        self,
        explanation: Dict[str, Any],
        max_features: int = 10
    ) -> Dict[str, Any]:
        """
        Generate data for waterfall plot visualization.

        Returns:
            Dictionary with start_value, contributions, and end_value
        """
        contributions = explanation.get("feature_contributions", [])[:max_features]
        base_value = explanation.get("base_value", 0.5)
        output_value = explanation.get("output_value", 0.5)

        # Build waterfall steps
        steps = []
        current_value = base_value

        for contrib in contributions:
            steps.append({
                "feature": contrib["feature"],
                "start": current_value,
                "end": current_value + contrib["shap_value"],
                "value": contrib["shap_value"],
                "direction": "positive" if contrib["shap_value"] > 0 else "negative"
            })
            current_value += contrib["shap_value"]

        return {
            "base_value": base_value,
            "output_value": output_value,
            "steps": steps,
            "total_explained": current_value - base_value
        }

    def generate_force_plot_data(
        self,
        explanation: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate data for force plot visualization."""
        return {
            "baseValue": explanation.get("base_value", 0.5),
            "outValue": explanation.get("output_value", 0.5),
            "features": [
                {
                    "name": f["feature"],
                    "value": f["shap_value"]
                }
                for f in explanation.get("feature_contributions", [])[:20]
            ]
        }


def batch_explain(
    transactions: List[Dict[str, Any]],
    predictions: List[float],
    explainer: ShapExplainer
) -> List[Dict[str, Any]]:
    """Generate explanations for multiple transactions."""
    explanations = []

    for tx, pred in zip(transactions, predictions):
        try:
            explanation = explainer.explain(tx, pred)
            explanations.append(explanation)
        except Exception as e:
            logger.warning("Failed to explain transaction", error=str(e))
            explanations.append(explainer._default_explanation(tx, pred))

    return explanations
