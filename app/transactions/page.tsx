"use client";

import { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { DashboardLayout } from '@/components/layout/dashboard-layout';
import { TransactionTable } from '@/components/transactions/transaction-table';
import type { Transaction, TransactionStatus } from '@/lib/types';

// Mock data for demo
const mockTransactions: Transaction[] = Array.from({ length: 50 }, (_, i) => ({
  id: `tx-${i}`,
  user_id: `user-1`,
  transaction_id: `TXN-${Date.now()}-${i}`,
  customer_id: `CUST-${Math.floor(Math.random() * 1000)}`,
  customer_name: ['John Doe', 'Jane Smith', 'Bob Johnson', 'Alice Williams'][i % 4],
  merchant_id: `MERCH-${Math.floor(Math.random() * 100)}`,
  merchant_name: ['Amazon', 'Walmart', 'Target', 'Best Buy', 'eBay'][i % 5],
  merchant_category: ['retail', 'electronics', 'grocery', 'travel'][i % 4],
  amount: Math.floor(Math.random() * 5000) + 50,
  currency: 'USD',
  transaction_type: ['purchase', 'transfer', 'withdrawal'][i % 3] as any,
  channel: ['web', 'mobile', 'pos'][i % 3] as any,
  country: ['US', 'GB', 'CA', 'AU'][i % 4],
  risk_score: Math.floor(Math.random() * 100),
  risk_label: ['safe', 'suspicious', 'fraudulent'][Math.min(2, Math.floor(i / 15))] as any,
  status: ['pending', 'approved', 'rejected', 'flagged'][i % 4] as any,
  transaction_timestamp: new Date(Date.now() - i * 3600000).toISOString(),
  created_at: new Date(Date.now() - i * 3600000).toISOString(),
}));

export default function TransactionsPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [total, setTotal] = useState(100);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);

  const pageSize = 20;

  useEffect(() => {
    setTimeout(() => {
      setTransactions(mockTransactions);
      setTotal(500);
      setLoading(false);
    }, 500);
  }, [page, searchParams]);

  const handleFilter = (filters: Record<string, string>) => {
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([k, v]) => {
      if (v) params.set(k, v);
    });
    router.push(`/transactions?${params.toString()}`);
  };

  const handleStatusUpdate = (id: string, status: TransactionStatus) => {
    setTransactions((prev) =>
      prev.map((tx) => (tx.id === id ? { ...tx, status } : tx))
    );
  };

  return (
    <DashboardLayout user={{ email: 'analyst@fraudguard.ai', full_name: 'Fraud Analyst', role: 'analyst' }}>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-white">Transactions</h1>
          <p className="text-slate-400 mt-1">
            View, search, and manage all processed transactions
          </p>
        </div>

        <TransactionTable
          transactions={transactions}
          total={total}
          page={page}
          pageSize={pageSize}
          onPageChange={setPage}
          onFilter={handleFilter}
          onStatusUpdate={handleStatusUpdate}
        />
      </div>
    </DashboardLayout>
  );
}
