"use client";

import { useState } from 'react';
import { motion } from 'framer-motion';
import {
  AlertTriangle,
  AlertCircle,
  Clock,
  CheckCircle,
  User,
  TrendingUp,
  AlertOctagon,
} from 'lucide-react';
import { DashboardLayout } from '@/components/layout/dashboard-layout';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { cn } from '@/lib/utils';

const severityColors = {
  critical: 'bg-red-500/10 text-red-400 border-red-500/20',
  high: 'bg-orange-500/10 text-orange-400 border-orange-500/20',
  medium: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
  low: 'bg-slate-500/10 text-slate-400 border-slate-500/20',
};

const severityIcons = {
  critical: AlertOctagon,
  high: AlertTriangle,
  medium: AlertCircle,
  low: Clock,
};

const statusColors = {
  open: 'bg-red-500/10 text-red-400 border-red-500/20',
  acknowledged: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
  investigating: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
  resolved: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  false_positive: 'bg-slate-500/10 text-slate-400 border-slate-500/20',
  escalated: 'bg-purple-500/10 text-purple-400 border-purple-500/20',
};

const mockAlerts = [
  {
    id: 'alert-1',
    alert_type: 'high_risk',
    severity: 'critical',
    title: 'Multiple High-Risk Transactions from Same Customer',
    description: 'Customer CUST-1234 has 5 transactions flagged as fraudulent in the last hour.',
    transaction_ids: ['TXN-001', 'TXN-002', 'TXN-003', 'TXN-004', 'TXN-005'],
    risk_score: 95,
    status: 'open',
    created_at: new Date(Date.now() - 1800000).toISOString(),
  },
  {
    id: 'alert-2',
    alert_type: 'velocity',
    severity: 'high',
    title: 'Unusual Velocity Pattern Detected',
    description: 'Merchant MERCH-567 shows 10x normal transaction volume in the last 6 hours.',
    transaction_ids: ['TXN-100', 'TXN-101'],
    risk_score: 85,
    status: 'investigating',
    created_at: new Date(Date.now() - 3600000).toISOString(),
  },
  {
    id: 'alert-3',
    alert_type: 'anomaly',
    severity: 'medium',
    title: 'Geographic Anomaly Detected',
    description: 'Transaction from new country (NG) for established customer CUST-789.',
    transaction_ids: ['TXN-200'],
    anomaly_score: 0.72,
    status: 'acknowledged',
    created_at: new Date(Date.now() - 7200000).toISOString(),
  },
  {
    id: 'alert-4',
    alert_type: 'pattern',
    severity: 'low',
    title: 'Round Amount Transaction Pattern',
    description: 'Customer CUST-456 made 3 transactions with round amounts ($1000, $2000, $3000).',
    transaction_ids: ['TXN-301', 'TXN-302', 'TXN-303'],
    risk_score: 45,
    status: 'resolved',
    created_at: new Date(Date.now() - 86400000).toISOString(),
  },
];

export default function AlertsPage() {
  const [alerts] = useState(mockAlerts);
  const [filter, setFilter] = useState<'all' | 'open' | 'investigating'>('all');

  const filteredAlerts = alerts.filter(a => {
    if (filter === 'all') return true;
    if (filter === 'open') return a.status === 'open';
    if (filter === 'investigating') return a.status === 'open' || a.status === 'investigating' || a.status === 'acknowledged';
    return true;
  });

  const openCount = alerts.filter(a => a.status === 'open').length;
  const criticalCount = alerts.filter(a => a.severity === 'critical' && a.status !== 'resolved').length;

  return (
    <DashboardLayout user={{ email: 'analyst@fraudguard.ai', full_name: 'Fraud Analyst', role: 'analyst' }}>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-white">Alert Center</h1>
            <p className="text-slate-400 mt-1">
              Monitor and respond to fraud alerts in real-time
            </p>
          </div>
        </div>

        {/* Summary Stats */}
        <div className="grid gap-4 md:grid-cols-4">
          <Card className="bg-slate-900 border-slate-800">
            <CardContent className="pt-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-400">Open Alerts</p>
                  <p className="text-3xl font-bold text-red-400">{openCount}</p>
                </div>
                <AlertTriangle className="h-8 w-8 text-red-400 opacity-50" />
              </div>
            </CardContent>
          </Card>
          <Card className="bg-slate-900 border-slate-800">
            <CardContent className="pt-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-400">Critical</p>
                  <p className="text-3xl font-bold text-orange-400">{criticalCount}</p>
                </div>
                <AlertOctagon className="h-8 w-8 text-orange-400 opacity-50" />
              </div>
            </CardContent>
          </Card>
          <Card className="bg-slate-900 border-slate-800">
            <CardContent className="pt-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-400">Avg Response</p>
                  <p className="text-3xl font-bold text-white">25m</p>
                </div>
                <Clock className="h-8 w-8 text-slate-500 opacity-50" />
              </div>
            </CardContent>
          </Card>
          <Card className="bg-slate-900 border-slate-800">
            <CardContent className="pt-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-400">Resolved Today</p>
                  <p className="text-3xl font-bold text-emerald-400">12</p>
                </div>
                <CheckCircle className="h-8 w-8 text-emerald-400 opacity-50" />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Alert Filters */}
        <div className="flex gap-2">
          {['all', 'open', 'investigating'].map((f) => (
            <Button
              key={f}
              variant={filter === f ? 'default' : 'outline'}
              onClick={() => setFilter(f as any)}
              className={cn(
                filter === f ? 'bg-emerald-500 hover:bg-emerald-600' : 'border-slate-700 text-slate-300'
              )}
            >
              {f.charAt(0).toUpperCase() + f.slice(1)}
              {f === 'open' && (
                <Badge className="ml-2 bg-red-500 text-white">{openCount}</Badge>
              )}
            </Button>
          ))}
        </div>

        {/* Alerts List */}
        <div className="space-y-4">
          {filteredAlerts.map((alert, i) => {
            const SeverityIcon = severityIcons[alert.severity as keyof typeof severityIcons];
            return (
              <motion.div
                key={alert.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.1 }}
              >
                <Card className={cn(
                  'bg-slate-900 border-slate-800 hover:border-slate-700 transition-colors',
                  alert.severity === 'critical' && alert.status === 'open' && 'border-red-500/30 ring-1 ring-red-500/10'
                )}>
                  <CardContent className="p-4">
                    <div className="flex items-start gap-4">
                      <div className={cn(
                        'p-2 rounded-lg',
                        severityColors[alert.severity as keyof typeof severityColors]
                      )}>
                        <SeverityIcon className="h-5 w-5" />
                      </div>

                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <h3 className="text-white font-medium">{alert.title}</h3>
                          <Badge className={severityColors[alert.severity as keyof typeof severityColors]}>
                            {alert.severity}
                          </Badge>
                          <Badge className={statusColors[alert.status as keyof typeof statusColors]}>
                            {alert.status}
                          </Badge>
                        </div>
                        <p className="text-sm text-slate-400 mb-2">{alert.description}</p>

                        <div className="flex items-center gap-4 text-xs text-slate-500">
                          <span>
                            {alert.transaction_ids.length} transaction{alert.transaction_ids.length > 1 ? 's' : ''}
                          </span>
                          <span>
                            {new Date(alert.created_at).toLocaleString()}
                          </span>
                          {alert.risk_score && (
                            <span className="flex items-center gap-1">
                              <TrendingUp className="h-3 w-3" />
                              Score: {alert.risk_score}
                            </span>
                          )}
                        </div>
                      </div>

                      <div className="flex items-center gap-2">
                        <Button size="sm" variant="outline" className="border-slate-700 text-slate-300">
                          View
                        </Button>
                        {alert.status === 'open' && (
                          <Button size="sm" className="bg-emerald-500 hover:bg-emerald-600">
                            Acknowledge
                          </Button>
                        )}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            );
          })}
        </div>
      </div>
    </DashboardLayout>
  );
}
