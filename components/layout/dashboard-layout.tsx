"use client";

import { ReactNode } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  Shield,
  Activity,
  FileText,
  AlertTriangle,
  Brain,
  BarChart3,
  Settings,
  LogOut,
  User,
  Bell,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Badge } from '@/components/ui/badge';

interface DashboardLayoutProps {
  children: ReactNode;
  user?: {
    email: string;
    full_name: string;
    role: string;
  };
}

const navItems = [
  { href: '/dashboard', label: 'Dashboard', icon: Activity },
  { href: '/transactions', label: 'Transactions', icon: FileText },
  { href: '/scoring', label: 'Score', icon: Shield },
  { href: '/alerts', label: 'Alerts', icon: AlertTriangle, badge: true },
  { href: '/models', label: 'Models', icon: Brain },
  { href: '/reports', label: 'Reports', icon: BarChart3 },
];

export function DashboardLayout({ children, user }: DashboardLayoutProps) {
  const pathname = usePathname();

  return (
    <div className="min-h-screen bg-slate-950">
      {/* Sidebar */}
      <aside className="fixed inset-y-0 left-0 w-64 bg-slate-900 border-r border-slate-800">
        <div className="flex h-full flex-col">
          {/* Logo */}
          <div className="flex h-16 items-center gap-3 px-6 border-b border-slate-800">
            <Shield className="h-8 w-8 text-emerald-500" />
            <span className="text-lg font-bold text-white">FraudGuard AI</span>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-4 py-6 space-y-2">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.href || pathname.startsWith(item.href + '/');
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    'flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-all duration-200',
                    isActive
                      ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                      : 'text-slate-400 hover:text-white hover:bg-slate-800'
                  )}
                >
                  <Icon className="h-5 w-5" />
                  <span>{item.label}</span>
                  {item.badge && (
                    <Badge variant="destructive" className="ml-auto text-xs px-2">
                      3
                    </Badge>
                  )}
                </Link>
              );
            })}
          </nav>

          {/* User section */}
          <div className="border-t border-slate-800 p-4">
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" className="w-full justify-start gap-3 px-3 py-2 text-slate-300 hover:text-white hover:bg-slate-800">
                  <Avatar className="h-8 w-8">
                    <AvatarFallback className="bg-slate-700 text-slate-300">
                      {user?.full_name?.charAt(0) || 'U'}
                    </AvatarFallback>
                  </Avatar>
                  <div className="flex flex-col items-start text-left">
                    <span className="text-sm font-medium">{user?.full_name || 'User'}</span>
                    <span className="text-xs text-slate-500">{user?.role || 'analyst'}</span>
                  </div>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-56 bg-slate-900 border-slate-800">
                <DropdownMenuLabel className="text-slate-300">My Account</DropdownMenuLabel>
                <DropdownMenuSeparator className="bg-slate-800" />
                <DropdownMenuItem className="text-slate-300 focus:text-white focus:bg-slate-800">
                  <User className="mr-2 h-4 w-4" />
                  Profile
                </DropdownMenuItem>
                <DropdownMenuItem className="text-slate-300 focus:text-white focus:bg-slate-800">
                  <Settings className="mr-2 h-4 w-4" />
                  Settings
                </DropdownMenuItem>
                <DropdownMenuSeparator className="bg-slate-800" />
                <DropdownMenuItem className="text-red-400 focus:text-red-300 focus:bg-slate-800">
                  <LogOut className="mr-2 h-4 w-4" />
                  Logout
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <main className="ml-64">
        {/* Top bar */}
        <header className="sticky top-0 z-10 h-16 bg-slate-900/80 backdrop-blur-sm border-b border-slate-800">
          <div className="flex items-center justify-between h-full px-6">
            <h1 className="text-lg font-semibold text-white">
              {navItems.find(item => pathname.startsWith(item.href))?.label || 'Dashboard'}
            </h1>
            <div className="flex items-center gap-4">
              <Button variant="ghost" size="icon" className="relative text-slate-400 hover:text-white">
                <Bell className="h-5 w-5" />
                <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"></span>
              </Button>
            </div>
          </div>
        </header>

        {/* Page content */}
        <div className="p-6">
          {children}
        </div>
      </main>
    </div>
  );
}
