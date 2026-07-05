"use client";

import { ReactNode } from 'react';
import { ArrowUpRight, ArrowDownRight, Minus } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { cn } from '@/lib/utils';

interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  change?: number;
  changeLabel?: string;
  icon: ReactNode;
  iconClassName?: string;
  variant?: 'default' | 'success' | 'warning' | 'danger';
}

export function MetricCard({
  title,
  value,
  subtitle,
  change,
  changeLabel,
  icon,
  iconClassName,
  variant = 'default',
}: MetricCardProps) {
  const changeIcon = change && change > 0 ? ArrowUpRight : change && change < 0 ? ArrowDownRight : Minus;
  const ChangeIcon = changeIcon;

  const variantStyles = {
    default: 'bg-slate-800 text-slate-300',
    success: 'bg-emerald-500/10 text-emerald-400',
    warning: 'bg-amber-500/10 text-amber-400',
    danger: 'bg-red-500/10 text-red-400',
  };

  return (
    <Card className="bg-slate-900 border-slate-800 hover:border-slate-700 transition-colors">
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-sm font-medium text-slate-400">{title}</CardTitle>
        <div className={cn('p-2 rounded-lg', variantStyles[variant], iconClassName)}>
          {icon}
        </div>
      </CardHeader>
      <CardContent>
        <div className="text-3xl font-bold text-white">{value}</div>
        {subtitle && <p className="text-xs text-slate-500 mt-1">{subtitle}</p>}
        {change !== undefined && (
          <div className="flex items-center gap-1 mt-2">
            <ChangeIcon
              className={cn(
                'h-4 w-4',
                change > 0 ? 'text-emerald-500' : change < 0 ? 'text-red-500' : 'text-slate-500'
              )}
            />
            <span
              className={cn(
                'text-xs font-medium',
                change > 0 ? 'text-emerald-500' : change < 0 ? 'text-red-500' : 'text-slate-500'
              )}
            >
              {Math.abs(change)}%
            </span>
            <span className="text-xs text-slate-500">{changeLabel || 'vs last period'}</span>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
