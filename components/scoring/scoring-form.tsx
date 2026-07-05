"use client";

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Separator } from '@/components/ui/separator';
import {
  Shield,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Clock,
  Zap,
  Upload,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import type { ScoringResponse, RiskLabel } from '@/lib/types';
import { ShapWaterfallChart } from '@/components/dashboard/charts';

const riskConfigs: Record<RiskLabel, {
  icon: typeof Shield;
  label: string;
  color: string;
  bg: string;
  border: string;
}> = {
  safe: {
    icon: CheckCircle,
    label: 'Safe',
    color: 'text-emerald-400',
    bg: 'bg-emerald-500/10',
    border: 'border-emerald-500/20',
  },
  suspicious: {
    icon: AlertTriangle,
    label: 'Suspicious',
    color: 'text-amber-400',
    bg: 'bg-amber-500/10',
    border: 'border-amber-500/20',
  },
  fraudulent: {
    icon: XCircle,
    label: 'Fraudulent',
    color: 'text-red-400',
    bg: 'bg-red-500/10',
    border: 'border-red-500/20',
  },
};

export function ScoringForm() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ScoringResponse | null>(null);

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setLoading(true);

    const formData = new FormData(e.currentTarget);
    const data = Object.fromEntries(formData.entries());

    // Mock result for demo
    setTimeout(() => {
      const mockResponse = {
        transaction_id: 'TXN-' + Math.random().toString(36).slice(2, 10).toUpperCase(),
        risk_score: 45 + Math.random() * 30,
        risk_label: ['safe', 'suspicious', 'fraudulent'][Math.floor(Math.random() * 3)] as RiskLabel,
        confidence: 0.7 + Math.random() * 0.25,
        model_id: 'model-001',
        model_type: 'xgboost',
        processing_time_ms: 23 + Math.random() * 50,
        anomaly_score: Math.random() * 0.3,
        anomaly_detected: Math.random() > 0.7,
        explanation: {
          base_value: 0.35,
          output_value: 0.65,
          feature_contributions: [
            { feature: 'amount', feature_value: parseFloat(data.amount as string) || 1000, shap_value: 0.15, abs_shap: 0.15 },
            { feature: 'is_night', feature_value: 0, shap_value: 0.08, abs_shap: 0.08 },
            { feature: 'tx_count_24h', feature_value: 3, shap_value: 0.12, abs_shap: 0.12 },
            { feature: 'customer_age_days', feature_value: 180, shap_value: -0.05, abs_shap: 0.05 },
            { feature: 'country_risk', feature_value: 0.1, shap_value: 0.02, abs_shap: 0.02 },
          ],
          top_factors: [
            { feature: 'amount', shap_value: 0.15, direction: 'increases', explanation: 'High transaction amount increases risk' },
            { feature: 'tx_count_24h', shap_value: 0.12, direction: 'increases', explanation: 'Multiple transactions in 24 hours' },
          ],
          model_id: 'model-001',
        },
      };
      setResult(mockResponse);
      setLoading(false);
    }, 800);
  };

  const config = result ? riskConfigs[result.risk_label] : null;

  return (
    <div className="grid gap-6 md:grid-cols-2">
      {/* Input Form */}
      <Card className="bg-slate-900 border-slate-800">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <Shield className="h-5 w-5 text-emerald-500" />
            Transaction Scoring
          </CardTitle>
          <CardDescription className="text-slate-400">
            Enter transaction details for real-time fraud risk assessment
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Tabs defaultValue="single">
            <TabsList className="bg-slate-800">
              <TabsTrigger value="single">Single Transaction</TabsTrigger>
              <TabsTrigger value="bulk">Bulk Upload</TabsTrigger>
            </TabsList>

            <TabsContent value="single" className="mt-4">
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label className="text-slate-300">Customer ID</Label>
                    <Input
                      name="customer_id"
                      placeholder="CUST-001"
                      className="bg-slate-800 border-slate-700 text-white"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label className="text-slate-300">Merchant ID</Label>
                    <Input
                      name="merchant_id"
                      placeholder="MERCH-001"
                      className="bg-slate-800 border-slate-700 text-white"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label className="text-slate-300">Amount</Label>
                    <Input
                      name="amount"
                      type="number"
                      step="0.01"
                      placeholder="1000.00"
                      className="bg-slate-800 border-slate-700 text-white"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label className="text-slate-300">Currency</Label>
                    <Select name="currency" defaultValue="USD">
                      <SelectTrigger className="bg-slate-800 border-slate-700 text-white">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent className="bg-slate-800 border-slate-700">
                        <SelectItem value="USD">USD</SelectItem>
                        <SelectItem value="EUR">EUR</SelectItem>
                        <SelectItem value="GBP">GBP</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label className="text-slate-300">Transaction Type</Label>
                    <Select name="transaction_type" defaultValue="purchase">
                      <SelectTrigger className="bg-slate-800 border-slate-700 text-white">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent className="bg-slate-800 border-slate-700">
                        <SelectItem value="purchase">Purchase</SelectItem>
                        <SelectItem value="transfer">Transfer</SelectItem>
                        <SelectItem value="withdrawal">Withdrawal</SelectItem>
                        <SelectItem value="deposit">Deposit</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label className="text-slate-300">Channel</Label>
                    <Select name="channel" defaultValue="web">
                      <SelectTrigger className="bg-slate-800 border-slate-700 text-white">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent className="bg-slate-800 border-slate-700">
                        <SelectItem value="web">Web</SelectItem>
                        <SelectItem value="mobile">Mobile</SelectItem>
                        <SelectItem value="pos">POS</SelectItem>
                        <SelectItem value="atm">ATM</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label className="text-slate-300">Country</Label>
                    <Input
                      name="country"
                      placeholder="US"
                      className="bg-slate-800 border-slate-700 text-white"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label className="text-slate-300">Device ID</Label>
                    <Input
                      name="device_id"
                      placeholder="DEV-001"
                      className="bg-slate-800 border-slate-700 text-white"
                    />
                  </div>
                </div>

                <Button
                  type="submit"
                  className="w-full bg-emerald-500 hover:bg-emerald-600"
                  disabled={loading}
                >
                  {loading ? (
                    <div className="flex items-center gap-2">
                      <div className="h-4 w-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                      Analyzing...
                    </div>
                  ) : (
                    <div className="flex items-center gap-2">
                      <Zap className="h-4 w-4" />
                      Score Transaction
                    </div>
                  )}
                </Button>
              </form>
            </TabsContent>

            <TabsContent value="bulk" className="mt-4">
              <div className="border-2 border-dashed border-slate-700 rounded-lg p-8 text-center">
                <Upload className="h-10 w-10 text-slate-500 mx-auto mb-4" />
                <p className="text-slate-300 mb-2">Upload CSV file with transactions</p>
                <p className="text-sm text-slate-500 mb-4">
                  Required columns: transaction_id, customer_id, merchant_id, amount
                </p>
                <Button variant="outline" className="border-slate-700 text-slate-300">
                  Select File
                </Button>
              </div>
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>

      {/* Results */}
      <div className="space-y-6">
        {result ? (
          <>
            {/* Risk Score Card */}
            <Card className={cn('border-2', config?.border, 'bg-slate-900')}>
              <CardHeader className="pb-4">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-white">Risk Assessment</CardTitle>
                  {config && (
                    <Badge className={cn(config.bg, config.color, config.border, 'border')}>
                      <config.icon className="h-4 w-4 mr-1" />
                      {config.label}
                    </Badge>
                  )}
                </div>
              </CardHeader>
              <CardContent>
                <div className="flex items-center justify-center mb-6">
                  <div className="relative">
                    <svg className="w-40 h-40 -rotate-90">
                      <circle
                        cx="80"
                        cy="80"
                        r="70"
                        fill="none"
                        stroke="#334155"
                        strokeWidth="12"
                      />
                      <circle
                        cx="80"
                        cy="80"
                        r="70"
                        fill="none"
                        stroke={
                          result.risk_score >= 70
                            ? '#ef4444'
                            : result.risk_score >= 40
                            ? '#f59e0b'
                            : '#10b981'
                        }
                        strokeWidth="12"
                        strokeDasharray={`${result.risk_score * 4.4} 440`}
                        strokeLinecap="round"
                      />
                    </svg>
                    <div className="absolute inset-0 flex flex-col items-center justify-center">
                      <span className="text-5xl font-bold text-white">
                        {Math.round(result.risk_score)}
                      </span>
                      <span className="text-sm text-slate-400">Risk Score</span>
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-4 text-center">
                  <div>
                    <p className="text-2xl font-bold text-white">
                      {(result.confidence * 100).toFixed(0)}%
                    </p>
                    <p className="text-sm text-slate-400">Confidence</p>
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-white">
                      {result.processing_time_ms.toFixed(0)}ms
                    </p>
                    <p className="text-sm text-slate-400">Latency</p>
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-white capitalize">
                      {result.model_type}
                    </p>
                    <p className="text-sm text-slate-400">Model</p>
                  </div>
                </div>

                {result.anomaly_detected && (
                  <div className="mt-4 p-3 bg-red-500/10 border border-red-500/20 rounded-lg">
                    <div className="flex items-center gap-2 text-red-400">
                      <AlertTriangle className="h-5 w-5" />
                      <span className="font-medium">Anomaly Detected</span>
                    </div>
                    <p className="text-sm text-red-300 mt-1">
                      Anomaly score: {(result.anomaly_score! * 100).toFixed(1)}%
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Explanation */}
            <Card className="bg-slate-900 border-slate-800">
              <CardHeader>
                <CardTitle className="text-white">Explanation</CardTitle>
                <CardDescription className="text-slate-400">
                  Key factors contributing to this risk score
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {result.explanation.top_factors.map((factor, i) => (
                    <div
                      key={i}
                      className={cn(
                        'p-3 rounded-lg border',
                        factor.direction === 'increases'
                          ? 'bg-red-500/5 border-red-500/20'
                          : 'bg-emerald-500/5 border-emerald-500/20'
                      )}
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span className="font-medium text-white capitalize">
                          {factor.feature.replace(/_/g, ' ')}
                        </span>
                        <span
                          className={cn(
                            'text-sm',
                            factor.direction === 'increases' ? 'text-red-400' : 'text-emerald-400'
                          )}
                        >
                          {factor.direction === 'increases' ? '+' : '-'}
                          {(Math.abs(factor.shap_value) * 100).toFixed(0)}%
                        </span>
                      </div>
                      <p className="text-sm text-slate-400">{factor.explanation}</p>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </>
        ) : (
          <Card className="bg-slate-900 border-slate-800">
            <CardContent className="flex flex-col items-center justify-center py-12 text-center">
              <Shield className="h-16 w-16 text-slate-700 mb-4" />
              <h3 className="text-lg font-medium text-white mb-2">No Score Yet</h3>
              <p className="text-slate-400">
                Enter transaction details and click Score to see the risk assessment
              </p>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
