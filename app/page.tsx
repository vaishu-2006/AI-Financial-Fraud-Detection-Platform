"use client";

import Link from 'next/link';
import { Shield, ArrowRight, Zap, Brain, BarChart3, Lock, Users } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { motion } from 'framer-motion';

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-950 via-slate-900 to-slate-950">
      {/* Navigation */}
      <header className="fixed top-0 left-0 right-0 z-50 bg-slate-950/80 backdrop-blur-md border-b border-slate-800">
        <div className="container mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Shield className="h-8 w-8 text-emerald-500" />
            <span className="text-xl font-bold text-white">FraudGuard AI</span>
          </div>
          <nav className="hidden md:flex items-center gap-6">
            <Link href="#features" className="text-slate-400 hover:text-white transition-colors">Features</Link>
            <Link href="#how-it-works" className="text-slate-400 hover:text-white transition-colors">How It Works</Link>
            <Link href="/dashboard" className="text-slate-400 hover:text-white transition-colors">Dashboard</Link>
          </nav>
          <div className="flex items-center gap-4">
            <Link href="/dashboard">
              <Button variant="ghost" className="text-slate-300 hover:text-white">
                Sign In
              </Button>
            </Link>
            <Link href="/dashboard">
              <Button className="bg-emerald-500 hover:bg-emerald-600">
                Get Started
              </Button>
            </Link>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="pt-32 pb-20 px-6">
        <div className="container mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-sm mb-8">
              <Zap className="h-4 w-4" />
              AI-Powered Fraud Detection
            </div>

            <h1 className="text-5xl md:text-6xl font-bold text-white mb-6 leading-tight">
              Detect Fraud in{' '}
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-cyan-400">
                Real-Time
              </span>
              {' '}with AI
            </h1>

            <p className="text-xl text-slate-400 max-w-3xl mx-auto mb-10">
              Protect your business with advanced machine learning models that score transactions,
              identify risks, and explain every decision with transparent AI explanations.
            </p>

            <div className="flex items-center justify-center gap-4">
              <Link href="/dashboard">
                <Button size="lg" className="bg-emerald-500 hover:bg-emerald-600 h-12 px-8">
                  Launch Dashboard
                  <ArrowRight className="ml-2 h-5 w-5" />
                </Button>
              </Link>
              <Link href="#how-it-works">
                <Button size="lg" variant="outline" className="border-slate-700 text-slate-300 hover:text-white h-12 px-8">
                  Learn More
                </Button>
              </Link>
            </div>
          </motion.div>

          {/* Demo Preview */}
          <motion.div
            initial={{ opacity: 0, y: 40 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.3 }}
            className="mt-16"
          >
            <div className="relative rounded-xl overflow-hidden border border-slate-800 bg-slate-900/50 shadow-2xl">
              <div className="absolute top-0 left-0 right-0 h-12 bg-slate-800/80 flex items-center px-4">
                <div className="flex gap-2">
                  <div className="w-3 h-3 rounded-full bg-red-500" />
                  <div className="w-3 h-3 rounded-full bg-amber-500" />
                  <div className="w-3 h-3 rounded-full bg-emerald-500" />
                </div>
              </div>
              <div className="pt-12 p-1">
                <div className="bg-slate-950 rounded-lg p-4 aspect-video flex items-center justify-center">
                  <div className="text-center">
                    <Shield className="h-20 w-20 text-emerald-500 mx-auto mb-4" />
                    <p className="text-slate-400">Interactive Dashboard Preview</p>
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-20 px-6">
        <div className="container mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
              Enterprise-Grade Fraud Detection
            </h2>
            <p className="text-slate-400 max-w-2xl mx-auto">
              Built with the latest ML techniques and designed for real-world deployment
            </p>
          </div>

          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {[
              {
                icon: Zap,
                title: 'Real-Time Scoring',
                description: 'Score transactions in under 100ms with optimized ML pipelines and caching.',
              },
              {
                icon: Brain,
                title: 'Explainable AI',
                description: 'Understand every prediction with SHAP values and feature contribution analysis.',
              },
              {
                icon: BarChart3,
                title: 'Model Management',
                description: 'Train, compare, and deploy multiple ML models with automatic selection.',
              },
              {
                icon: Lock,
                title: 'Role-Based Access',
                description: 'Secure multi-tenant access with analyst, manager, and admin roles.',
              },
              {
                icon: Users,
                title: 'Team Collaboration',
                description: 'Assign alerts, review transactions, and track resolution progress.',
              },
              {
                icon: Shield,
                title: 'Anomaly Detection',
                description: 'Catch novel fraud patterns with Isolation Forest and autoencoders.',
              },
            ].map((feature, i) => (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.1 }}
                viewport={{ once: true }}
              >
                <div className="p-6 rounded-xl bg-slate-900/50 border border-slate-800 hover:border-emerald-500/30 transition-colors h-full">
                  <div className="p-3 rounded-lg bg-emerald-500/10 w-fit mb-4">
                    <feature.icon className="h-6 w-6 text-emerald-500" />
                  </div>
                  <h3 className="text-xl font-semibold text-white mb-2">{feature.title}</h3>
                  <p className="text-slate-400">{feature.description}</p>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section id="how-it-works" className="py-20 px-6 bg-slate-900/50">
        <div className="container mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
              How It Works
            </h2>
            <p className="text-slate-400">Four steps to protect your business</p>
          </div>

          <div className="grid gap-8 md:grid-cols-4">
            {[
              { step: 1, title: 'Upload Data', description: 'Import transactions via CSV or API' },
              { step: 2, title: 'Train Models', description: 'Auto-train multiple ML models' },
              { step: 3, title: 'Score Transactions', description: 'Real-time risk assessment' },
              { step: 4, title: 'Respond to Alerts', description: 'Take action on high-risk transactions' },
            ].map((item, i) => (
              <motion.div
                key={item.step}
                initial={{ opacity: 0, x: -20 }}
                whileInView={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.15 }}
                viewport={{ once: true }}
                className="text-center"
              >
                <div className="w-16 h-16 rounded-full bg-emerald-500/10 border-2 border-emerald-500/30 flex items-center justify-center mx-auto mb-4">
                  <span className="text-2xl font-bold text-emerald-400">{item.step}</span>
                </div>
                <h3 className="text-lg font-semibold text-white mb-2">{item.title}</h3>
                <p className="text-slate-400 text-sm">{item.description}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-6">
        <div className="container mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
          >
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-slate-800 text-emerald-400 text-sm mb-6">
              Ready to get started?
            </div>
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-6">
              Start Detecting Fraud Today
            </h2>
            <p className="text-slate-400 max-w-xl mx-auto mb-8">
              Join thousands of businesses using AI to protect against fraud.
              No credit card required.
            </p>
            <Link href="/dashboard">
              <Button size="lg" className="bg-emerald-500 hover:bg-emerald-600 h-12 px-8">
                Launch Dashboard
                <ArrowRight className="ml-2 h-5 w-5" />
              </Button>
            </Link>
          </motion.div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-slate-800 py-8 px-6">
        <div className="container mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <Shield className="h-6 w-6 text-emerald-500" />
            <span className="text-white font-semibold">FraudGuard AI</span>
          </div>
          <p className="text-slate-500 text-sm">
            Built with AI for detecting financial fraud. Portfolio project.
          </p>
        </div>
      </footer>
    </div>
  );
}
