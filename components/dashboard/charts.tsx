"use client";

import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  Legend,
  LineChart,
  Line,
} from 'recharts';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';

const COLORS = {
  safe: '#10b981',
  suspicious: '#f59e0b',
  fraudulent: '#ef4444',
  primary: '#3b82f6',
  secondary: '#8b5cf6',
};

interface RiskDistributionChartProps {
  data: { name: string; value: number; color: string }[];
}

export function RiskDistributionChart({ data }: RiskDistributionChartProps) {
  return (
    <Card className="bg-slate-900 border-slate-800">
      <CardHeader>
        <CardTitle className="text-white">Risk Distribution</CardTitle>
        <CardDescription className="text-slate-400">
          Distribution of transactions by risk label
        </CardDescription>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={250}>
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              innerRadius={60}
              outerRadius={100}
              paddingAngle={2}
              dataKey="value"
              label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
              labelLine={false}
            >
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Pie>
            <Tooltip
              contentStyle={{
                backgroundColor: '#1e293b',
                border: '1px solid #334155',
                borderRadius: '8px',
              }}
              labelStyle={{ color: '#fff' }}
              itemStyle={{ color: '#94a3b8' }}
            />
          </PieChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}

interface VolumeChartProps {
  data: Array<{ date: string; volume: number; fraud_count: number }>;
}

export function TransactionVolumeChart({ data }: VolumeChartProps) {
  return (
    <Card className="bg-slate-900 border-slate-800">
      <CardHeader>
        <CardTitle className="text-white">Transaction Volume</CardTitle>
        <CardDescription className="text-slate-400">
          Daily transaction volume and fraud counts
        </CardDescription>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <AreaChart data={data}>
            <defs>
              <linearGradient id="colorVolume" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="colorFraud" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis
              dataKey="date"
              tick={{ fill: '#94a3b8', fontSize: 12 }}
              tickLine={{ stroke: '#334155' }}
              axisLine={{ stroke: '#334155' }}
            />
            <YAxis
              tick={{ fill: '#94a3b8', fontSize: 12 }}
              tickLine={{ stroke: '#334155' }}
              axisLine={{ stroke: '#334155' }}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#1e293b',
                border: '1px solid #334155',
                borderRadius: '8px',
              }}
              labelStyle={{ color: '#fff' }}
              itemStyle={{ color: '#94a3b8' }}
            />
            <Area
              type="monotone"
              dataKey="volume"
              stroke="#3b82f6"
              fillOpacity={1}
              fill="url(#colorVolume)"
              name="Volume"
            />
            <Area
              type="monotone"
              dataKey="fraud_count"
              stroke="#ef4444"
              fillOpacity={1}
              fill="url(#colorFraud)"
              name="Fraud"
            />
          </AreaChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}

interface FeatureImportanceChartProps {
  data: Array<{ feature: string; importance: number }>;
}

export function FeatureImportanceChart({ data }: FeatureImportanceChartProps) {
  return (
    <Card className="bg-slate-900 border-slate-800">
      <CardHeader>
        <CardTitle className="text-white">Feature Importance</CardTitle>
        <CardDescription className="text-slate-400">
          Top features contributing to fraud detection
        </CardDescription>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={data} layout="vertical">
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis
              type="number"
              tick={{ fill: '#94a3b8', fontSize: 12 }}
              tickLine={{ stroke: '#334155' }}
              axisLine={{ stroke: '#334155' }}
            />
            <YAxis
              type="category"
              dataKey="feature"
              tick={{ fill: '#94a3b8', fontSize: 10 }}
              tickLine={{ stroke: '#334155' }}
              axisLine={{ stroke: '#334155' }}
              width={120}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#1e293b',
                border: '1px solid #334155',
                borderRadius: '8px',
              }}
              labelStyle={{ color: '#fff' }}
              itemStyle={{ color: '#94a3b8' }}
            />
            <Bar dataKey="importance" fill="#10b981" radius={[0, 4, 4, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}

interface ShapWaterfallChartProps {
  baseValue: number;
  outputValue: number;
  steps: Array<{
    feature: string;
    start: number;
    end: number;
    value: number;
    direction: string;
  }>;
}

export function ShapWaterfallChart({ baseValue, outputValue, steps }: ShapWaterfallChartProps) {
  const data = steps.map((step, i) => ({
    name: step.feature,
    value: step.value,
    fill: step.direction === 'positive' ? '#ef4444' : '#10b981',
  }));

  // Add base and output
  data.unshift({ name: 'Base', value: baseValue, fill: '#64748b' });
  data.push({ name: 'Output', value: outputValue, fill: '#3b82f6' });

  return (
    <Card className="bg-slate-900 border-slate-800">
      <CardHeader>
        <CardTitle className="text-white">Prediction Breakdown</CardTitle>
        <CardDescription className="text-slate-400">
          How each feature contributed to the risk score
        </CardDescription>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={data} layout="vertical">
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis
              type="number"
              domain={[0, 100]}
              tick={{ fill: '#94a3b8', fontSize: 12 }}
              tickLine={{ stroke: '#334155' }}
              axisLine={{ stroke: '#334155' }}
            />
            <YAxis
              type="category"
              dataKey="name"
              tick={{ fill: '#94a3b8', fontSize: 10 }}
              tickLine={{ stroke: '#334155' }}
              axisLine={{ stroke: '#334155' }}
              width={120}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#1e293b',
                border: '1px solid #334155',
                borderRadius: '8px',
              }}
            />
            <Bar dataKey="value" radius={[0, 4, 4, 0]}>
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.fill} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}

interface ModelComparisonChartProps {
  data: Array<{
    model_type: string;
    f1_score: number;
    precision: number;
    recall: number;
    roc_auc: number;
  }>;
}

export function ModelComparisonChart({ data }: ModelComparisonChartProps) {
  return (
    <Card className="bg-slate-900 border-slate-800">
      <CardHeader>
        <CardTitle className="text-white">Model Performance Comparison</CardTitle>
        <CardDescription className="text-slate-400">
          Compare metrics across trained models
        </CardDescription>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis
              dataKey="model_type"
              tick={{ fill: '#94a3b8', fontSize: 12 }}
              tickLine={{ stroke: '#334155' }}
              axisLine={{ stroke: '#334155' }}
            />
            <YAxis
              domain={[0, 1]}
              tick={{ fill: '#94a3b8', fontSize: 12 }}
              tickLine={{ stroke: '#334155' }}
              axisLine={{ stroke: '#334155' }}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#1e293b',
                border: '1px solid #334155',
                borderRadius: '8px',
              }}
            />
            <Legend
              wrapperStyle={{ color: '#94a3b8' }}
            />
            <Bar dataKey="f1_score" name="F1 Score" fill="#3b82f6" />
            <Bar dataKey="precision" name="Precision" fill="#10b981" />
            <Bar dataKey="recall" name="Recall" fill="#f59e0b" />
            <Bar dataKey="roc_auc" name="ROC AUC" fill="#8b5cf6" />
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
