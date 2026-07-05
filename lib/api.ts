// API Client for Fraud Detection Backend

import type {
  AuthTokens,
  User,
  Transaction,
  TransactionListResponse,
  ScoringRequest,
  ScoringResponse,
  Model,
  Alert,
  DashboardMetrics,
  RiskDistribution,
  TimeSeriesPoint,
  TrainingConfig,
  ApiResponse
} from './types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

class ApiClient {
  private baseUrl: string;
  private accessToken: string | null = null;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
    if (typeof window !== 'undefined') {
      this.accessToken = localStorage.getItem('access_token');
    }
  }

  setAccessToken(token: string) {
    this.accessToken = token;
    if (typeof window !== 'undefined') {
      localStorage.setItem('access_token', token);
    }
  }

  clearAccessToken() {
    this.accessToken = null;
    if (typeof window !== 'undefined') {
      localStorage.removeItem('access_token');
    }
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };

    if (this.accessToken) {
      headers['Authorization'] = `Bearer ${this.accessToken}`;
    }

    if (options.headers) {
      Object.assign(headers, options.headers);
    }

    try {
      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        ...options,
        headers,
      });

      const data = await response.json();

      if (!response.ok) {
        return { error: data.detail || data.error || 'Request failed' };
      }

      return { data };
    } catch (error) {
      return { error: error instanceof Error ? error.message : 'Network error' };
    }
  }

  // Auth endpoints
  async login(email: string, password: string): Promise<ApiResponse<AuthTokens>> {
    const result = await this.request<AuthTokens>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
    if (result.data) {
      this.setAccessToken(result.data.access_token);
    }
    return result;
  }

  async register(email: string, password: string, full_name: string, role: string): Promise<ApiResponse<User>> {
    return this.request<User>('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email, password, full_name, role }),
    });
  }

  async logout(): Promise<ApiResponse<void>> {
    const result = await this.request<void>('/auth/logout', { method: 'POST' });
    this.clearAccessToken();
    return result;
  }

  async getCurrentUser(): Promise<ApiResponse<User>> {
    return this.request<User>('/auth/me');
  }

  // Transaction endpoints
  async getTransactions(params: Record<string, string | number>): Promise<ApiResponse<TransactionListResponse>> {
    const query = new URLSearchParams(
      Object.entries(params)
        .filter(([_, v]) => v !== undefined && v !== '')
        .map(([k, v]) => [k, String(v)])
    ).toString();
    return this.request<TransactionListResponse>(`/transactions?${query}`);
  }

  async getTransaction(id: string): Promise<ApiResponse<Transaction>> {
    return this.request<Transaction>(`/transactions/${id}`);
  }

  async createTransaction(transaction: Partial<Transaction>): Promise<ApiResponse<Transaction>> {
    return this.request<Transaction>('/transactions', {
      method: 'POST',
      body: JSON.stringify(transaction),
    });
  }

  async uploadTransactionsCSV(file: File): Promise<ApiResponse<{ imported: number; errors: unknown[] }>> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${this.baseUrl}/transactions/upload`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${this.accessToken}`,
      },
      body: formData,
    });

    const data = await response.json();
    return response.ok ? { data } : { error: data.detail };
  }

  async updateTransactionStatus(id: string, status: string, notes?: string): Promise<ApiResponse<Transaction>> {
    return this.request<Transaction>(`/transactions/${id}`, {
      method: 'PATCH',
      body: JSON.stringify({ status, review_notes: notes }),
    });
  }

  async exportTransactionsCSV(params: Record<string, string>): Promise<Blob> {
    const query = new URLSearchParams(params).toString();
    const response = await fetch(`${this.baseUrl}/transactions/export/csv?${query}`, {
      headers: { Authorization: `Bearer ${this.accessToken}` },
    });
    return response.blob();
  }

  // Scoring endpoints
  async scoreTransaction(transaction: ScoringRequest): Promise<ApiResponse<ScoringResponse>> {
    return this.request<ScoringResponse>('/scoring/single', {
      method: 'POST',
      body: JSON.stringify(transaction),
    });
  }

  async getShapExplanation(transactionId: string): Promise<ApiResponse<ScoringResponse['explanation']>> {
    return this.request<ScoringResponse['explanation']>(`/scoring/explain/${transactionId}`);
  }

  // Model endpoints
  async getModels(): Promise<ApiResponse<Model[]>> {
    return this.request<Model[]>('/models');
  }

  async getActiveModel(): Promise<ApiResponse<Model>> {
    return this.request<Model>('/models/active');
  }

  async getModel(id: string): Promise<ApiResponse<Model>> {
    return this.request<Model>(`/models/${id}`);
  }

  async deployModel(id: string): Promise<ApiResponse<{ message: string }>> {
    return this.request<{ message: string }>(`/models/${id}/deploy`, { method: 'POST' });
  }

  async startTraining(config: TrainingConfig): Promise<ApiResponse<{ job_id: string; message: string }>> {
    return this.request<{ job_id: string; message: string }>('/models/train', {
      method: 'POST',
      body: JSON.stringify(config),
    });
  }

  // Alerts endpoints
  async getAlerts(params: Record<string, string>): Promise<ApiResponse<Alert[]>> {
    const query = new URLSearchParams(params).toString();
    return this.request<Alert[]>(`/alerts?${query}`);
  }

  async updateAlert(id: string, data: Partial<Alert>): Promise<ApiResponse<Alert>> {
    return this.request<Alert>(`/alerts/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  }

  // Reports endpoints
  async getDashboardMetrics(days: number = 7): Promise<ApiResponse<DashboardMetrics>> {
    return this.request<DashboardMetrics>(`/reports/dashboard?days=${days}`);
  }

  async getRiskDistribution(days: number = 30): Promise<ApiResponse<RiskDistribution>> {
    return this.request<RiskDistribution>(`/reports/risk-distribution?days=${days}`);
  }

  async getTimeSeriesData(days: number = 30): Promise<ApiResponse<TimeSeriesPoint[]>> {
    return this.request<TimeSeriesPoint[]>(`/reports/timeseries?days=${days}`);
  }
}

export const api = new ApiClient();
export default api;
