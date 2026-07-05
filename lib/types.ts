// TypeScript interfaces for Fraud Detection Platform

export type UserRole = 'analyst' | 'manager' | 'admin';
export type RiskLabel = 'safe' | 'suspicious' | 'fraudulent';
export type TransactionStatus = 'pending' | 'reviewing' | 'approved' | 'rejected' | 'flagged';
export type TransactionType = 'purchase' | 'transfer' | 'withdrawal' | 'deposit' | 'payment';
export type Channel = 'web' | 'mobile' | 'pos' | 'atm' | 'api';
export type AlertSeverity = 'low' | 'medium' | 'high' | 'critical';
export type AlertStatus = 'open' | 'acknowledged' | 'investigating' | 'resolved' | 'false_positive' | 'escalated';
export type ModelType = 'logistic_regression' | 'random_forest' | 'xgboost' | 'lightgbm' | 'neural_network' | 'ensemble';

// User
export interface User {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  department?: string;
  is_active: boolean;
  last_login?: string;
  created_at: string;
}

// Auth
export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

// Transaction
export interface Transaction {
  id: string;
  user_id: string;
  transaction_id: string;
  reference_number?: string;
  customer_id: string;
  customer_name?: string;
  merchant_id: string;
  merchant_name?: string;
  merchant_category?: string;
  amount: number;
  currency: string;
  transaction_type: TransactionType;
  latitude?: number;
  longitude?: number;
  country?: string;
  city?: string;
  ip_address?: string;
  device_id?: string;
  device_type?: string;
  channel: Channel;
  transaction_timestamp: string;
  local_hour?: number;
  day_of_week?: number;
  features?: Record<string, number>;
  risk_score?: number;
  risk_label?: RiskLabel;
  model_id?: string;
  status: TransactionStatus;
  reviewed_by?: string;
  reviewed_at?: string;
  review_notes?: string;
  created_at: string;
}

export interface TransactionListResponse {
  transactions: Transaction[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

// Scoring
export interface ScoringRequest {
  transaction_id: string;
  customer_id: string;
  merchant_id: string;
  amount: number;
  currency?: string;
  transaction_type?: TransactionType;
  latitude?: number;
  longitude?: number;
  country?: string;
  city?: string;
  ip_address?: string;
  device_id?: string;
  device_type?: string;
  channel?: Channel;
  transaction_timestamp: string;
  merchant_category?: string;
}

export interface ShapExplanation {
  base_value: number;
  output_value: number;
  feature_contributions: FeatureContribution[];
  top_factors: TopFactor[];
  model_id: string;
}

export interface FeatureContribution {
  feature: string;
  feature_value: number;
  shap_value: number;
  abs_shap: number;
}

export interface TopFactor {
  feature: string;
  shap_value: number;
  direction: string;
  explanation: string;
}

export interface ScoringResponse {
  transaction_id: string;
  risk_score: number;
  risk_label: RiskLabel;
  confidence: number;
  model_id: string;
  model_type: string;
  explanation: ShapExplanation;
  anomaly_score?: number;
  anomaly_detected: boolean;
  processing_time_ms: number;
}

// Model
export interface Model {
  id: string;
  user_id: string;
  name: string;
  version: string;
  model_type: ModelType;
  training_config: Record<string, unknown>;
  feature_columns: string[];
  metrics: ModelMetrics;
  f1_score?: number;
  precision_score?: number;
  recall_score?: number;
  roc_auc?: number;
  pr_auc?: number;
  training_samples?: number;
  validation_samples?: number;
  fraud_rate?: number;
  training_duration_seconds?: number;
  model_path?: string;
  scaler_path?: string;
  explainer_path?: string;
  status: 'training' | 'validating' | 'deployed' | 'deprecated' | 'failed';
  is_active: boolean;
  deployed_at?: string;
  deployed_by?: string;
  trained_at: string;
  created_at: string;
}

export interface ModelMetrics {
  f1_score?: number;
  precision?: number;
  recall?: number;
  roc_auc?: number;
  pr_auc?: number;
  confusion_matrix?: number[][];
  feature_importance?: Record<string, number>;
  feature_importance_top10?: Array<{ feature: string; importance: number }>;
}

// Alert
export interface Alert {
  id: string;
  user_id: string;
  alert_type: 'high_risk' | 'anomaly' | 'velocity' | 'pattern' | 'threshold';
  severity: AlertSeverity;
  title: string;
  description?: string;
  transaction_ids: string[];
  model_id?: string;
  rule_id?: string;
  risk_score?: number;
  anomaly_score?: number;
  status: AlertStatus;
  priority: number;
  assigned_to?: string;
  assigned_at?: string;
  resolved_by?: string;
  resolved_at?: string;
  resolution_notes?: string;
  resolution_type?: string;
  occurred_at: string;
  created_at: string;
}

// Dashboard
export interface DashboardMetrics {
  total_transactions: number;
  fraud_detected: number;
  false_positives: number;
  detection_rate: number;
  avg_risk_score: number;
  total_amount_monitored: number;
  fraud_amount_prevented: number;
}

export interface RiskDistribution {
  safe: number;
  suspicious: number;
  fraudulent: number;
}

export interface TimeSeriesPoint {
  date: string;
  volume: number;
  fraud_count: number;
  avg_amount: number;
}

// Training Config
export interface TrainingConfig {
  model_name: string;
  model_types: ModelType[];
  selection_metric: 'f1_score' | 'roc_auc' | 'precision' | 'recall' | 'pr_auc';
  start_date?: string;
  end_date?: string;
  train_test_split: number;
  stratified_split: boolean;
  time_based_split: boolean;
  feature_selection: boolean;
  n_features?: number;
  include_anomaly_features: boolean;
  hyperparameter_tuning: boolean;
  n_trials: number;
  cv_folds: number;
  sampling_strategy: 'smote' | 'undersample' | 'oversample' | 'none';
  use_class_weights: boolean;
  random_seed: number;
}

// API Response wrapper
export interface ApiResponse<T> {
  data?: T;
  error?: string;
  message?: string;
}
