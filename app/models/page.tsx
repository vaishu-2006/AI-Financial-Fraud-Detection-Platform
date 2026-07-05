"use client";

import { useState } from 'react';
import { motion } from 'framer-motion';
import {
  Brain,
  Play,
  CheckCircle,
  Clock,
  AlertCircle,
  TrendingUp,
  BarChart3,
  Settings,
  Download,
} from 'lucide-react';
import { DashboardLayout } from '@/components/layout/dashboard-layout';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ModelComparisonChart } from '@/components/dashboard/charts';
import { cn } from '@/lib/utils';
import type { Model } from '@/lib/types';

// Mock models data
const mockModels: Model[] = [
  {
    id: 'model-1',
    user_id: 'user-1',
    name: 'XGBoost Fraud Detector',
    version: 'xgboost_20240101',
    model_type: 'xgboost',
    training_config: {},
    feature_columns: ['amount', 'velocity', 'hour', 'channel'],
    metrics: {},
    f1_score: 0.94,
    precision_score: 0.92,
    recall_score: 0.96,
    roc_auc: 0.98,
    training_samples: 50000,
    fraud_rate: 0.02,
    status: 'deployed',
    is_active: true,
    trained_at: new Date().toISOString(),
    created_at: new Date().toISOString(),
  },
  {
    id: 'model-2',
    user_id: 'user-1',
    name: 'LightGBM Detector',
    version: 'lightgbm_20240102',
    model_type: 'lightgbm',
    training_config: {},
    feature_columns: ['amount', 'velocity', 'hour', 'channel', 'country'],
    metrics: {},
    f1_score: 0.91,
    precision_score: 0.90,
    recall_score: 0.93,
    roc_auc: 0.96,
    training_samples: 50000,
    fraud_rate: 0.02,
    status: 'validating',
    is_active: false,
    trained_at: new Date().toISOString(),
    created_at: new Date().toISOString(),
  },
  {
    id: 'model-3',
    user_id: 'user-1',
    name: 'Random Forest',
    version: 'rf_20240103',
    model_type: 'random_forest',
    training_config: {},
    feature_columns: ['amount', 'velocity', 'hour'],
    metrics: {},
    f1_score: 0.88,
    precision_score: 0.86,
    recall_score: 0.90,
    roc_auc: 0.94,
    training_samples: 45000,
    fraud_rate: 0.02,
    status: 'deprecated',
    is_active: false,
    trained_at: new Date(Date.now() - 86400000 * 7).toISOString(),
    created_at: new Date(Date.now() - 86400000 * 7).toISOString(),
  },
];

const modelComparisonData = [
  { model_type: 'XGBoost', f1_score: 0.94, precision: 0.92, recall: 0.96, roc_auc: 0.98 },
  { model_type: 'LightGBM', f1_score: 0.91, precision: 0.90, recall: 0.93, roc_auc: 0.96 },
  { model_type: 'Random Forest', f1_score: 0.88, precision: 0.86, recall: 0.90, roc_auc: 0.94 },
];

export default function ModelsPage() {
  const [models] = useState(mockModels);

  const activeModel = models.find(m => m.is_active);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'deployed': return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20';
      case 'training': return 'bg-blue-500/10 text-blue-400 border-blue-500/20';
      case 'validating': return 'bg-amber-500/10 text-amber-400 border-amber-500/20';
      case 'deprecated': return 'bg-slate-500/10 text-slate-400 border-slate-500/20';
      default: return 'bg-slate-500/10 text-slate-400 border-slate-500/20';
    }
  };

  return (
    <DashboardLayout user={{ email: 'analyst@fraudguard.ai', full_name: 'Fraud Analyst', role: 'analyst' }}>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-white">Model Management</h1>
            <p className="text-slate-400 mt-1">
              Train, compare, and deploy ML models for fraud detection
            </p>
          </div>
          <Button className="bg-emerald-500 hover:bg-emerald-600">
            <Play className="h-4 w-4 mr-2" />
            Start Training
          </Button>
        </div>

        {/* Active Model Card */}
        {activeModel && (
          <Card className="bg-slate-900 border-emerald-500/30 ring-1 ring-emerald-500/20">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Brain className="h-8 w-8 text-emerald-500" />
                  <div>
                    <CardTitle className="text-white">{activeModel.name}</CardTitle>
                    <CardDescription className="text-slate-400">
                      Currently deployed • Version {activeModel.version}
                    </CardDescription>
                  </div>
                </div>
                <Badge className="bg-emerald-500/10 text-emerald-400 border-emerald-500/20">
                  <CheckCircle className="h-3 w-3 mr-1" />
                  Active
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-5 gap-4">
                <div className="p-3 bg-slate-800 rounded-lg text-center">
                  <p className="text-2xl font-bold text-emerald-400">
                    {(activeModel.f1_score! * 100).toFixed(1)}%
                  </p>
                  <p className="text-xs text-slate-400">F1 Score</p>
                </div>
                <div className="p-3 bg-slate-800 rounded-lg text-center">
                  <p className="text-2xl font-bold text-white">
                    {(activeModel.precision_score! * 100).toFixed(1)}%
                  </p>
                  <p className="text-xs text-slate-400">Precision</p>
                </div>
                <div className="p-3 bg-slate-800 rounded-lg text-center">
                  <p className="text-2xl font-bold text-white">
                    {(activeModel.recall_score! * 100).toFixed(1)}%
                  </p>
                  <p className="text-xs text-slate-400">Recall</p>
                </div>
                <div className="p-3 bg-slate-800 rounded-lg text-center">
                  <p className="text-2xl font-bold text-white">
                    {(activeModel.roc_auc! * 100).toFixed(1)}%
                  </p>
                  <p className="text-xs text-slate-400">ROC AUC</p>
                </div>
                <div className="p-3 bg-slate-800 rounded-lg text-center">
                  <p className="text-2xl font-bold text-white">
                    {activeModel.training_samples?.toLocaleString()}
                  </p>
                  <p className="text-xs text-slate-400">Samples</p>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Tabs */}
        <Tabs defaultValue="models">
          <TabsList className="bg-slate-800">
            <TabsTrigger value="models">All Models</TabsTrigger>
            <TabsTrigger value="comparison">Comparison</TabsTrigger>
            <TabsTrigger value="training">Training Config</TabsTrigger>
          </TabsList>

          <TabsContent value="models" className="mt-4 space-y-4">
            {models.map((model) => (
              <motion.div
                key={model.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
              >
                <Card className={cn(
                  'bg-slate-900 border-slate-800',
                  model.is_active && 'border-emerald-500/30 ring-1 ring-emerald-500/20'
                )}>
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-4">
                        <div className={cn(
                          'p-2 rounded-lg',
                          model.is_active ? 'bg-emerald-500/10' : 'bg-slate-800'
                        )}>
                          <Brain className={cn(
                            'h-6 w-6',
                            model.is_active ? 'text-emerald-500' : 'text-slate-400'
                          )} />
                        </div>
                        <div>
                          <h3 className="text-white font-medium">{model.name}</h3>
                          <div className="flex items-center gap-2 text-sm text-slate-400">
                            <span>{model.model_type}</span>
                            <span>•</span>
                            <span>v{model.version.split('_').pop()}</span>
                            <span>•</span>
                            <span>{new Date(model.trained_at).toLocaleDateString()}</span>
                          </div>
                        </div>
                      </div>

                      <div className="flex items-center gap-4">
                        <Badge className={getStatusColor(model.status)}>
                          {model.status}
                        </Badge>

                        <div className="flex gap-2">
                          <Button size="sm" variant="outline" className="border-slate-700 text-slate-300">
                            <BarChart3 className="h-4 w-4 mr-1" />
                            View
                          </Button>
                          {!model.is_active && model.status !== 'training' && (
                            <Button size="sm" className="bg-emerald-500 hover:bg-emerald-600">
                              Deploy
                            </Button>
                          )}
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </TabsContent>

          <TabsContent value="comparison" className="mt-4">
            <ModelComparisonChart data={modelComparisonData} />
          </TabsContent>

          <TabsContent value="training" className="mt-4">
            <Card className="bg-slate-900 border-slate-800">
              <CardHeader>
                <CardTitle className="text-white">New Training Configuration</CardTitle>
                <CardDescription className="text-slate-400">
                  Configure and start a new model training job
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="text-center py-12 text-slate-400">
                  <Settings className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>Training configuration form would go here</p>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </DashboardLayout>
  );
}
