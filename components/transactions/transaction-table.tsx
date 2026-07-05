"use client";

import { useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  ChevronLeft,
  ChevronRight,
  Search,
  Filter,
  MoreHorizontal,
  Eye,
  CheckCircle,
  XCircle,
  Flag,
  Download,
  ArrowUpDown,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import type { Transaction, RiskLabel, TransactionStatus } from '@/lib/types';

interface TransactionTableProps {
  transactions: Transaction[];
  total: number;
  page: number;
  pageSize: number;
  onPageChange: (page: number) => void;
  onFilter: (filters: Record<string, string>) => void;
  onStatusUpdate: (id: string, status: TransactionStatus) => void;
}

const riskColors: Record<RiskLabel, string> = {
  safe: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  suspicious: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
  fraudulent: 'bg-red-500/10 text-red-400 border-red-500/20',
};

const statusColors: Record<TransactionStatus, string> = {
  pending: 'bg-slate-500/10 text-slate-400 border-slate-500/20',
  reviewing: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
  approved: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  rejected: 'bg-red-500/10 text-red-400 border-red-500/20',
  flagged: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
};

export function TransactionTable({
  transactions,
  total,
  page,
  pageSize,
  onPageChange,
  onFilter,
  onStatusUpdate,
}: TransactionTableProps) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [search, setSearch] = useState('');

  const totalPages = Math.ceil(total / pageSize);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    onFilter({ search });
  };

  const formatCurrency = (amount: number, currency = 'USD') => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency,
    }).format(amount);
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <Card className="bg-slate-900 border-slate-800">
      <CardHeader className="pb-4">
        <div className="flex items-center justify-between">
          <CardTitle className="text-white">Transactions</CardTitle>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" className="border-slate-700 text-slate-300">
              <Download className="h-4 w-4 mr-2" />
              Export
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {/* Filters */}
        <div className="flex flex-wrap items-center gap-3 mb-4">
          <form onSubmit={handleSearch} className="flex items-center gap-2">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
              <Input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search transactions..."
                className="pl-9 w-64 bg-slate-800 border-slate-700 text-white placeholder:text-slate-500"
              />
            </div>
            <Button type="submit" size="sm" variant="secondary">
              Search
            </Button>
          </form>

          <Select
            value={searchParams.get('risk_label') || ''}
            onValueChange={(v) => onFilter({ risk_label: v })}
          >
            <SelectTrigger className="w-32 bg-slate-800 border-slate-700 text-white">
              <SelectValue placeholder="Risk Label" />
            </SelectTrigger>
            <SelectContent className="bg-slate-800 border-slate-700">
              <SelectItem value="">All Labels</SelectItem>
              <SelectItem value="safe">Safe</SelectItem>
              <SelectItem value="suspicious">Suspicious</SelectItem>
              <SelectItem value="fraudulent">Fraudulent</SelectItem>
            </SelectContent>
          </Select>

          <Select
            value={searchParams.get('status') || ''}
            onValueChange={(v) => onFilter({ status: v })}
          >
            <SelectTrigger className="w-32 bg-slate-800 border-slate-700 text-white">
              <SelectValue placeholder="Status" />
            </SelectTrigger>
            <SelectContent className="bg-slate-800 border-slate-700">
              <SelectItem value="">All Status</SelectItem>
              <SelectItem value="pending">Pending</SelectItem>
              <SelectItem value="reviewing">Reviewing</SelectItem>
              <SelectItem value="approved">Approved</SelectItem>
              <SelectItem value="rejected">Rejected</SelectItem>
              <SelectItem value="flagged">Flagged</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Table */}
        <div className="rounded-lg border border-slate-800 overflow-hidden">
          <Table>
            <TableHeader className="bg-slate-800/50">
              <TableRow className="hover:bg-slate-800/50 border-slate-700">
                <TableHead className="text-slate-400 font-medium">
                  <Button variant="ghost" size="sm" className="h-8 -ml-3 text-slate-400 hover:text-white">
                    Transaction ID
                    <ArrowUpDown className="ml-2 h-4 w-4" />
                  </Button>
                </TableHead>
                <TableHead className="text-slate-400 font-medium">Customer</TableHead>
                <TableHead className="text-slate-400 font-medium">Merchant</TableHead>
                <TableHead className="text-slate-400 font-medium text-right">Amount</TableHead>
                <TableHead className="text-slate-400 font-medium">Risk Score</TableHead>
                <TableHead className="text-slate-400 font-medium">Label</TableHead>
                <TableHead className="text-slate-400 font-medium">Status</TableHead>
                <TableHead className="text-slate-400 font-medium">Timestamp</TableHead>
                <TableHead className="text-slate-400 font-medium w-12"></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {transactions.map((tx) => (
                <TableRow
                  key={tx.id}
                  className="hover:bg-slate-800/30 border-slate-800 cursor-pointer"
                  onClick={() => router.push(`/transactions/${tx.id}`)}
                >
                  <TableCell className="font-mono text-sm text-white">
                    {tx.transaction_id.slice(0, 8)}...
                  </TableCell>
                  <TableCell className="text-slate-300">
                    <div className="flex flex-col">
                      <span className="text-sm">{tx.customer_name || tx.customer_id}</span>
                      <span className="text-xs text-slate-500">{tx.customer_id}</span>
                    </div>
                  </TableCell>
                  <TableCell className="text-slate-300">
                    <span className="text-sm">{tx.merchant_name || tx.merchant_id}</span>
                  </TableCell>
                  <TableCell className="text-right">
                    <span className="text-white font-medium">
                      {formatCurrency(tx.amount, tx.currency)}
                    </span>
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <div className="w-16 h-2 bg-slate-700 rounded-full overflow-hidden">
                        <div
                          className={cn(
                            'h-full rounded-full',
                            (tx.risk_score || 0) >= 70
                              ? 'bg-red-500'
                              : (tx.risk_score || 0) >= 40
                              ? 'bg-amber-500'
                              : 'bg-emerald-500'
                          )}
                          style={{ width: `${tx.risk_score || 0}%` }}
                        />
                      </div>
                      <span className="text-sm text-white">{tx.risk_score?.toFixed(0) || '-'}</span>
                    </div>
                  </TableCell>
                  <TableCell>
                    {tx.risk_label && (
                      <Badge className={riskColors[tx.risk_label]}>
                        {tx.risk_label}
                      </Badge>
                    )}
                  </TableCell>
                  <TableCell>
                    <Badge className={statusColors[tx.status]}>
                      {tx.status}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-slate-400 text-sm">
                    {formatDate(tx.transaction_timestamp)}
                  </TableCell>
                  <TableCell>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild onClick={(e) => e.stopPropagation()}>
                        <Button variant="ghost" size="sm" className="h-8 w-8 p-0 text-slate-400">
                          <MoreHorizontal className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent
                        align="end"
                        className="bg-slate-800 border-slate-700"
                        onClick={(e) => e.stopPropagation()}
                      >
                        <DropdownMenuItem
                          className="text-slate-300 focus:text-white focus:bg-slate-700"
                          onClick={() => router.push(`/transactions/${tx.id}`)}
                        >
                          <Eye className="mr-2 h-4 w-4" />
                          View Details
                        </DropdownMenuItem>
                        <DropdownMenuItem
                          className="text-slate-300 focus:text-white focus:bg-slate-700"
                          onClick={() => onStatusUpdate(tx.id, 'approved')}
                        >
                          <CheckCircle className="mr-2 h-4 w-4" />
                          Approve
                        </DropdownMenuItem>
                        <DropdownMenuItem
                          className="text-slate-300 focus:text-white focus:bg-slate-700"
                          onClick={() => onStatusUpdate(tx.id, 'rejected')}
                        >
                          <XCircle className="mr-2 h-4 w-4" />
                          Reject
                        </DropdownMenuItem>
                        <DropdownMenuItem
                          className="text-slate-300 focus:text-white focus:bg-slate-700"
                          onClick={() => onStatusUpdate(tx.id, 'flagged')}
                        >
                          <Flag className="mr-2 h-4 w-4" />
                          Flag for Review
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>

        {/* Pagination */}
        <div className="flex items-center justify-between mt-4">
          <p className="text-sm text-slate-400">
            Showing {((page - 1) * pageSize) + 1} to {Math.min(page * pageSize, total)} of {total} transactions
          </p>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              disabled={page <= 1}
              onClick={() => onPageChange(page - 1)}
              className="border-slate-700 text-slate-300"
            >
              <ChevronLeft className="h-4 w-4" />
              Previous
            </Button>
            <div className="flex items-center gap-1">
              {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                const pageNum = page - 2 + i;
                if (pageNum < 1 || pageNum > totalPages) return null;
                return (
                  <Button
                    key={pageNum}
                    variant={pageNum === page ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => onPageChange(pageNum)}
                    className={cn(
                      'w-8 h-8 p-0',
                      pageNum === page
                        ? 'bg-emerald-500 hover:bg-emerald-600'
                        : 'border-slate-700 text-slate-300'
                    )}
                  >
                    {pageNum}
                  </Button>
                );
              })}
            </div>
            <Button
              variant="outline"
              size="sm"
              disabled={page >= totalPages}
              onClick={() => onPageChange(page + 1)}
              className="border-slate-700 text-slate-300"
            >
              Next
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
