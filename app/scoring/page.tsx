"use client";

import { DashboardLayout } from '@/components/layout/dashboard-layout';
import { ScoringForm } from '@/components/scoring/scoring-form';

export default function ScoringPage() {
  return (
    <DashboardLayout user={{ email: 'analyst@fraudguard.ai', full_name: 'Fraud Analyst', role: 'analyst' }}>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-white">Real-time Scoring</h1>
          <p className="text-slate-400 mt-1">
            Instantly assess fraud risk for any transaction
          </p>
        </div>

        <ScoringForm />
      </div>
    </DashboardLayout>
  );
}
