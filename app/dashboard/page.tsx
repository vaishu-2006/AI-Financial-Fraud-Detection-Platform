"use client";

import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import {
  Shield,
  AlertTriangle,
  DollarSign,
  Activity,
  TrendingUp,
  TrendingDown,
  UserCheck,
  Clock,
} from 'lucide-react';
import { DashboardLayout } from '@/components/layout/dashboard-layout';
import { MetricCard } from '@/components/dashboard/metric-cards';
import {
  RiskDistributionChart,
  TransactionVolumeChart,
  FeatureImportanceChart,
} from '@/components/dashboard/charts';
import type { DashboardMetrics, RiskDistribution, TimeSeriesPoint } from '@/lib/types';

// Mock data for demo
const mockMetrics: DashboardMetrics = {
  total_transactions: 12847,
  fraud_detected: 127,
  false_positives: 23,
  detection_rate: 0.991,
  avg_risk_score: 32.5,
  total_amount_monitored: 8473921.45,
  fraud_amount_prevented: 234567.89,
};

const mockRiskData = [
  { name: 'Safe', value: 11234, color: '#10b981' },
  { name: 'Suspicious', value: 1486, color: '#f59e0b' },
  { name: 'Fraudulent', value: 127, color: '#ef4444' },
];

const mockTimeSeriesData: TimeSeriesPoint[] = Array.from({ length: 30 }, (_, i) => ({
  date: new Date(Date.now() - (29 - i) * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
  volume: Math.floor(300 + Math.random() * 200),
  fraud_count: Math.floor(Math.random() * 8),
  avg_amount: 500 + Math.random() * 500,
}));

const mockFeatureImportance = [
  { feature: 'Transaction Amount', importance: 0.18 },
  { feature: 'Velocity (1h)', importance: 0.14 },
  { feature: 'Customer Age', importance: 0.12 },
  { feature: 'Time of Day', importance: 0.10 },
  { feature: 'Device Type', importance: 0.09 },
  { feature: 'Merchant Category', importance: 0.08 },
  { feature: 'Country Risk', importance: 0.07 },
  { feature: 'Channel', importance: 0.06 },
];

export default function DashboardPage() {
  const [metrics, setMetrics] = useState(mockMetrics);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Simulate API call
    setTimeout(() => setIsLoading(false), 500);
  }, []);

  return (
    <DashboardLayout user={{ email: 'analyst@fraudguard.ai', full_name: 'Fraud Analyst', role: 'analyst' }}>
      <div className="space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold text-white">Dashboard</h1>
          <p className="text-slate-400 mt-1">
            Real-time fraud detection monitoring and analytics
          </p>
        </div>

        {/* Metric Cards */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
          >
            <MetricCard
              title="Total Transactions"
              value={metrics.total_transactions.toLocaleString()}
              subtitle="Last 7 days"
              change={12.5}
              changeLabel="vs last week"
              icon={<Activity className="h-5 w-5" />}
              variant="default"
            />
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
          >
            <MetricCard
              title="Fraud Detected"
              value={metrics.fraud_detected.toString()}
              subtitle={`${metrics.false_positives} false positives`}
              change={-8.3}
              changeLabel="vs last week"
              icon={<Shield className="h-5 w-5" />}
              variant="success"
            />
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
          >
            <MetricCard
              title="Detection Rate"
              value={`${(metrics.detection_rate * 100).toFixed(1)}%`}
              subtitle="True positive rate"
              change={2.1}
              changeLabel="improvement"
              icon={<TrendingUp className="h-5 w-5" />}
              variant="success"
            />
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
          >
            <MetricCard
              title="Avg Risk Score"
              value={metrics.avg_risk_score.toFixed(1)}
              subtitle="Out of 100"
              change={-3.2}
              changeLabel="vs last week"
              icon={<AlertTriangle className="h-5 w-5" />}
              variant="warning"
            />
          </motion.div>
        </div>

        {/* Second Row Metrics */}
        <div className="grid gap-4 md:grid-cols-3">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5 }}
          >
            <MetricCard
              title="Amount Monitored"
              value={`$${(metrics.total_amount_monitored / 1000000).toFixed(2)}M`}
              subtitle="Total transaction value"
              icon={<DollarSign className="h-5 w-5" />}
            />
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.6 }}
          >
            <MetricCard
              title="Fraud Prevented"
              value={`$${(metrics.fraud_amount_prevented / 1000).toFixed(0)}K`}
              subtitle="Estimated savings"
              change={15.4}
              changeLabel="vs last week"
              icon={<UserCheck className="h-5 w-5" />}
              variant="success"
            />
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.7 }}
          >
            <MetricCard
              title="Avg Processing Time"
              value="45ms"
              subtitle="Per transaction"
              icon={<Clock className="h-5 w-5" />}
              variant="default"
            />
          </motion.div>
        </div>

        {/* Charts Row */}
        <div className="grid gap-6 lg:grid-cols-2">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.8 }}
          >
            <TransactionVolumeChart data={mockTimeSeriesData} />
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.9 }}
          >
            <RiskDistributionChart data={mockRiskData} />
          </motion.div>
        </div>

        {/* Feature Importance */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 1.0 }}
        >
          <FeatureImportanceChart data={mockFeatureImportance} />
        </motion.div>
      </div>
    </DashboardLayout>
  );
}
