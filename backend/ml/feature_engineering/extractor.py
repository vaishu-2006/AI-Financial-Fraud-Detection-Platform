"""
Feature Engineering for Fraud Detection

Computes fraud-specific features:
- Velocity features (transaction frequency, amount patterns)
- Behavioral features (customer/merchant patterns)
- Time-based features (hour, day, weekend patterns)
- Location features (distance, country risk)
- Device features (device age, type patterns)
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
import math

@dataclass
class FeatureConfig:
    """Configuration for feature engineering."""
    # Velocity features
    velocity_windows_hours: List[int] = None  # [1, 6, 24, 168]
    velocity_amount_windows: bool = True

    # Customer features
    customer_history_days: int = 90
    customer_percentiles: bool = True

    # Merchant features
    merchant_fraud_rate_window_days: int = 30

    # Time features
    include_cyclical_time: bool = True
    include_weekend_flags: bool = True

    # Location features
    calculate_distances: bool = True
    country_risk_scores: Dict[str, float] = None

    # Device features
    device_trust_scores: bool = True
    new_device_threshold_days: int = 7

    def __post_init__(self):
        if self.velocity_windows_hours is None:
            self.velocity_windows_hours = [1, 6, 24, 168]
        if self.country_risk_scores is None:
            # Default country risk scores (example values)
            self.country_risk_scores = {
                "US": 0.1, "GB": 0.1, "CA": 0.1, "AU": 0.1,
                "DE": 0.12, "FR": 0.12, "JP": 0.11, "SG": 0.11,
                "NG": 0.8, "RU": 0.6, "UA": 0.5, "BY": 0.6
            }


class FeatureExtractor:
    """Extract and compute fraud detection features."""

    def __init__(self, config: Optional[FeatureConfig] = None):
        self.config = config or FeatureConfig()
        self.feature_names = []

    def extract_features(
        self,
        transaction: Dict[str, Any],
        historical_data: Optional[pd.DataFrame] = None,
        customer_history: Optional[pd.DataFrame] = None,
        merchant_history: Optional[pd.DataFrame] = None
    ) -> Dict[str, float]:
        """
        Extract all features for a single transaction.

        Args:
            transaction: Current transaction data
            historical_data: Recent transactions for velocity calculations
            customer_history: Customer's transaction history
            merchant_history: Merchant's transaction history

        Returns:
            Dictionary of feature name -> value
        """
        features = {}

        # Amount features
        features.update(self._extract_amount_features(transaction))

        # Time features
        features.update(self._extract_time_features(transaction))

        # Velocity features
        if historical_data is not None:
            features.update(self._extract_velocity_features(transaction, historical_data))

        # Customer behavior features
        if customer_history is not None:
            features.update(self._extract_customer_features(transaction, customer_history))

        # Merchant features
        if merchant_history is not None:
            features.update(self._extract_merchant_features(transaction, merchant_history))

        # Location features
        features.update(self._extract_location_features(transaction))

        # Device features
        features.update(self._extract_device_features(transaction))

        # Cross features
        features.update(self._extract_cross_features(transaction, features))

        self.feature_names = list(features.keys())
        return features

    def _extract_amount_features(self, tx: Dict) -> Dict[str, float]:
        """Extract amount-related features."""
        amount = float(tx.get("amount", 0))
        currency = tx.get("currency", "USD")

        features = {
            "amount": amount,
            "amount_log": np.log1p(amount),
            "amount_rounded": float(amount == round(amount)),
            "amount_near_limit": float(amount > 900 and amount < 1000),
            "amount_high_value": float(amount > 5000),
            "amount_very_high_value": float(amount > 10000),
        }

        # Transaction type encoding
        tx_type = tx.get("transaction_type", "purchase")
        features["is_purchase"] = float(tx_type == "purchase")
        features["is_transfer"] = float(tx_type == "transfer")
        features["is_withdrawal"] = float(tx_type == "withdrawal")

        return features

    def _extract_time_features(self, tx: Dict) -> Dict[str, float]:
        """Extract time-based features."""
        ts = tx.get("transaction_timestamp")
        if isinstance(ts, str):
            ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        elif ts is None:
            ts = datetime.utcnow()

        hour = tx.get("local_hour", ts.hour)
        dow = tx.get("day_of_week", ts.weekday())

        features = {
            "hour": float(hour),
            "day_of_week": float(dow),
            "is_night": float(hour >= 22 or hour <= 6),
            "is_morning": float(6 <= hour <= 12),
            "is_afternoon": float(12 <= hour <= 18),
            "is_evening": float(18 <= hour <= 22),
            "is_weekend": float(dow >= 5),
            "is_business_hours": float(9 <= hour <= 17 and dow < 5),
        }

        # Cyclical encoding for time
        if self.config.include_cyclical_time:
            features["hour_sin"] = np.sin(2 * np.pi * hour / 24)
            features["hour_cos"] = np.cos(2 * np.pi * hour / 24)
            features["dow_sin"] = np.sin(2 * np.pi * dow / 7)
            features["dow_cos"] = np.cos(2 * np.pi * dow / 7)

        return features

    def _extract_velocity_features(
        self,
        tx: Dict,
        historical: pd.DataFrame
    ) -> Dict[str, float]:
        """Extract velocity (transaction frequency) features."""
        features = {}
        tx_time = tx.get("transaction_timestamp")
        if isinstance(tx_time, str):
            tx_time = pd.to_datetime(tx_time)
        customer_id = tx.get("customer_id")

        if customer_id and not historical.empty:
            customer_txs = historical[historical.get("customer_id") == customer_id]

            for window_h in self.config.velocity_windows_hours:
                window_start = tx_time - timedelta(hours=window_h)
                recent = customer_txs[pd.to_datetime(customer_txs.get("transaction_timestamp", customer_txs.index)) >= window_start]

                features[f"tx_count_{window_h}h"] = float(len(recent))
                features[f"tx_amount_sum_{window_h}h"] = float(recent.get("amount", pd.Series([0])).sum())
                features[f"tx_amount_mean_{window_h}h"] = float(recent.get("amount", pd.Series([0])).mean())

                # Unique merchants in window
                if "merchant_id" in recent.columns:
                    features[f"unique_merchants_{window_h}h"] = float(recent["merchant_id"].nunique())

        return features

    def _extract_customer_features(
        self,
        tx: Dict,
        history: pd.DataFrame
    ) -> Dict[str, float]:
        """Extract customer behavior features."""
        features = {}
        customer_id = tx.get("customer_id")
        amount = float(tx.get("amount", 0))

        if not history.empty:
            amounts = history.get("amount", pd.Series([0]))

            features["customer_tx_count"] = float(len(history))
            features["customer_total_amount"] = float(amounts.sum())
            features["customer_avg_amount"] = float(amounts.mean())
            features["customer_std_amount"] = float(amounts.std()) if len(amounts) > 1 else 0

            # Z-score of current amount
            if features["customer_std_amount"] > 0:
                features["amount_zscore"] = (amount - features["customer_avg_amount"]) / features["customer_std_amount"]
            else:
                features["amount_zscore"] = 0

            # Percentile features
            if self.config.customer_percentiles:
                features["amount_percentile"] = float((amounts < amount).mean())

            # Days since first transaction
            if "transaction_timestamp" in history.columns:
                dates = pd.to_datetime(history["transaction_timestamp"])
                features["customer_age_days"] = (dates.max() - dates.min()).days
                features["days_since_last_tx"] = (datetime.utcnow() - dates.max()).days

        # Customer ID encoding (hash-based feature)
        features["customer_is_new"] = float(not history or len(history) == 0)

        return features

    def _extract_merchant_features(
        self,
        tx: Dict,
        history: pd.DataFrame
    ) -> Dict[str, float]:
        """Extract merchant-related features."""
        features = {}
        merchant_id = tx.get("merchant_id")

        if not history.empty:
            # Merchant transaction volume
            features["merchant_tx_count"] = float(len(history))
            features["merchant_avg_amount"] = float(history.get("amount", pd.Series([0])).mean())

            # Merchant category encoding
            category = tx.get("merchant_category", "unknown")
            # One-hot encode common high-risk categories
            high_risk_categories = ["gambling", "adult", "crypto", "money_transfer", "jewelry", "electronics"]
            for cat in high_risk_categories:
                features[f"category_{cat}"] = float(category.lower() == cat)

            # Merchant fraud rate (if labels available)
            if "is_fraud" in history.columns:
                features["merchant_fraud_rate"] = float(history["is_fraud"].mean())
        else:
            features["merchant_tx_count"] = 0
            features["merchant_avg_amount"] = 0
            features["merchant_fraud_rate"] = 0

        return features

    def _extract_location_features(self, tx: Dict) -> Dict[str, float]:
        """Extract location-based features."""
        features = {}
        country = tx.get("country", "unknown")

        # Country risk score
        features["country_risk"] = self.config.country_risk_scores.get(country, 0.3)
        features["country_known"] = float(country in self.config.country_risk_scores)

        # Latitude/longitude validity
        lat = tx.get("latitude")
        lon = tx.get("longitude")
        features["has_location"] = float(lat is not None and lon is not None)

        if lat and lon:
            features["latitude"] = float(lat)
            features["longitude"] = float(lon)

        # IP address features
        ip = tx.get("ip_address")
        features["has_ip"] = float(ip is not None)

        # Distance from previous would be calculated if we had previous location
        features["location_distance_km"] = 0  # Placeholder

        return features

    def _extract_device_features(self, tx: Dict) -> Dict[str, float]:
        """Extract device-related features."""
        features = {}
        device_id = tx.get("device_id")
        device_type = tx.get("device_type", "unknown")

        features["has_device_id"] = float(device_id is not None)
        features["device_is_mobile"] = float(device_type.lower() in ["mobile", "android", "ios", "iphone", "android"])
        features["device_is_desktop"] = float(device_type.lower() in ["desktop", "pc", "mac"])
        features["device_is_web"] = float(device_type.lower() == "web")

        # Channel encoding
        channel = tx.get("channel", "web")
        features["channel_web"] = float(channel == "web")
        features["channel_mobile"] = float(channel == "mobile")
        features["channel_atm"] = float(channel == "atm")
        features["channel_pos"] = float(channel == "pos")
        features["channel_api"] = float(channel == "api")

        return features

    def _extract_cross_features(
        self,
        tx: Dict,
        existing_features: Dict[str, float]
    ) -> Dict[str, float]:
        """Extract cross-feature interactions."""
        features = {}

        # Amount * time interaction
        features["amount_night_interaction"] = existing_features.get("amount", 0) * existing_features.get("is_night", 0)
        features["amount_weekend_interaction"] = existing_features.get("amount", 0) * existing_features.get("is_weekend", 0)

        # Location * amount
        features["high_amount_foreign"] = existing_features.get("amount_very_high_value", 0) * (1 - existing_features.get("country_risk", 0.3))

        # Velocity * amount
        if "tx_count_1h" in existing_features:
            features["velocity_amount_1h"] = existing_features.get("tx_count_1h", 0) * existing_features.get("amount", 0)

        return features


def compute_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Compute distance between two coordinates using Haversine formula."""
    R = 6371  # Earth's radius in km

    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))

    return R * c


class FeatureStore:
    """Feature store for caching computed features."""

    def __init__(self, ttl_seconds: int = 3600):
        self.cache = {}
        self.ttl_seconds = ttl_seconds

    def get_customer_features(self, customer_id: str) -> Optional[Dict]:
        """Get cached customer features."""
        key = f"customer:{customer_id}"
        return self.cache.get(key, {}).get("data")

    def set_customer_features(self, customer_id: str, features: Dict):
        """Cache customer features."""
        key = f"customer:{customer_id}"
        self.cache[key] = {
            "data": features,
            "expires_at": datetime.utcnow() + timedelta(seconds=self.ttl_seconds)
        }

    def get_merchant_features(self, merchant_id: str) -> Optional[Dict]:
        """Get cached merchant features."""
        key = f"merchant:{merchant_id}"
        return self.cache.get(key, {}).get("data")

    def set_merchant_features(self, merchant_id: str, features: Dict):
        """Cache merchant features."""
        key = f"merchant:{merchant_id}"
        self.cache[key] = {
            "data": features,
            "expires_at": datetime.utcnow() + timedelta(seconds=self.ttl_seconds)
        }

    def cleanup_expired(self):
        """Remove expired entries."""
        now = datetime.utcnow()
        expired_keys = [
            k for k, v in self.cache.items()
            if v.get("expires_at", now) < now
        ]
        for key in expired_keys:
            del self.cache[key]
