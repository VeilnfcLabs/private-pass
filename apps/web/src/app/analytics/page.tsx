"use client";

import React, { useState } from "react";
import { Sidebar } from "@/components/layout/sidebar";
import { Navbar } from "@/components/layout/navbar";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Select } from "@/components/ui/select";
import { cn } from "@/lib/utils";
import { showToast } from "@/components/ui/toast";
import { BarChart3, Eye, Globe, Smartphone, Shield, Users, Activity, Download, TrendingUp } from "lucide-react";

const mockAnalytics = {
  totalScans: 12847,
  uniqueIPs: 3421,
  scansToday: 89,
  scansThisWeek: 612,
  topAgents: [
    { agent: "Chrome 120", count: 4832, pct: 37.6 },
    { agent: "Safari 17", count: 2914, pct: 22.7 },
    { agent: "Firefox 121", count: 1823, pct: 14.2 },
    { agent: "Instagram", count: 1201, pct: 9.3 },
    { agent: "WeChat", count: 876, pct: 6.8 },
  ],
  topReferrers: [
    { source: "Direct", count: 5421, pct: 42.2 },
    { source: "Twitter/X", count: 2134, pct: 16.6 },
    { source: "LinkedIn", count: 1652, pct: 12.9 },
    { source: "WhatsApp", count: 1087, pct: 8.5 },
  ],
  scansOverTime: [
    { date: "Mon", count: 1842 },
    { date: "Tue", count: 2103 },
    { date: "Wed", count: 1956 },
    { date: "Thu", count: 2247 },
    { date: "Fri", count: 1983 },
    { date: "Sat", count: 1421 },
    { date: "Sun", count: 1295 },
  ],
  privacyScore: 87,
  dataRetention: "30 days",
  gdprCompliant: true,
  kenyaDpaCompliant: true,
};

export default function AnalyticsPage() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [privacyMode, setPrivacyMode] = useState("standard");
  const [timeRange, setTimeRange] = useState("7d");

  const maxScan = Math.max(...mockAnalytics.scansOverTime.map((s) => s.count));

  return (
    <div className="flex h-screen overflow-hidden bg-surface">
      <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Navbar onMenuClick={() => setSidebarOpen(true)} />
        <main className="flex-1 overflow-y-auto p-4 lg:p-6">
          <div className="max-w-7xl mx-auto space-y-6">
            <div className="animate-fade-in flex items-center justify-between">
              <div>
                <h1 className="text-2xl font-bold text-text-primary">QR Analytics</h1>
                <p className="text-text-secondary mt-1">Privacy-first scan analytics and insights</p>
              </div>
              <div className="flex gap-2">
                <Select
                  value={privacyMode}
                  onChange={(e) => setPrivacyMode(e.target.value)}
                  options={[
                    { value: "standard", label: "Standard" },
                    { value: "privacy", label: "Privacy" },
                    { value: "aggregate_only", label: "Aggregate Only" },
                  ]}
                />
                <Select
                  value={timeRange}
                  onChange={(e) => setTimeRange(e.target.value)}
                  options={[
                    { value: "24h", label: "24 Hours" },
                    { value: "7d", label: "7 Days" },
                    { value: "30d", label: "30 Days" },
                    { value: "90d", label: "90 Days" },
                  ]}
                />
              </div>
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {[
                { label: "Total Scans", value: mockAnalytics.totalScans.toLocaleString(), icon: <Eye size={20} />, color: "text-primary-400" },
                { label: "Unique IPs", value: mockAnalytics.uniqueIPs.toLocaleString(), icon: <Users size={20} />, color: "text-secondary-400" },
                { label: "Scans Today", value: mockAnalytics.scansToday, icon: <Activity size={20} />, color: "text-emerald-400" },
                { label: "Privacy Score", value: `${mockAnalytics.privacyScore}%`, icon: <Shield size={20} />, color: "text-amber-400" },
              ].map((stat, i) => (
                <Card key={i}>
                  <div className="flex items-center gap-3">
                    <div className={cn("w-10 h-10 rounded-lg bg-surface-elevated flex items-center justify-center", stat.color)}>{stat.icon}</div>
                    <div>
                      <p className="text-2xl font-bold text-text-primary">{stat.value}</p>
                      <p className="text-xs text-text-secondary">{stat.label}</p>
                    </div>
                  </div>
                </Card>
              ))}
            </div>

            {/* Scans Over Time Bar Chart */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle>Scans Over Time</CardTitle>
                  <TrendingUp size={16} className="text-text-secondary" />
                </div>
              </CardHeader>
              <CardContent>
                <div className="flex items-end gap-2 h-32">
                  {mockAnalytics.scansOverTime.map((day, i) => (
                    <div key={i} className="flex-1 flex flex-col items-center gap-1">
                      <div
                        className="w-full bg-gradient-to-t from-primary-500/80 to-primary-400/60 rounded-t transition-all hover:opacity-80"
                        style={{ height: `${(day.count / maxScan) * 100}%`, minHeight: "8px" }}
                      />
                      <span className="text-xs text-text-muted">{day.date}</span>
                      <span className="text-xs text-text-secondary font-medium">{day.count}</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Top Agents & Referrers */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <div className="flex items-center gap-2">
                    <Smartphone size={16} className="text-text-secondary" />
                    <CardTitle>Top User Agents</CardTitle>
                  </div>
                </CardHeader>
                <CardContent className="space-y-3">
                  {mockAnalytics.topAgents.map((agent, i) => (
                    <div key={i} className="flex items-center gap-3">
                      <span className="text-sm text-text-muted w-6">{i + 1}.</span>
                      <div className="flex-1">
                        <div className="flex justify-between text-sm">
                          <span className="text-text-primary">{agent.agent}</span>
                          <span className="text-text-secondary">{agent.count.toLocaleString()}</span>
                        </div>
                        <div className="w-full bg-surface-elevated rounded-full h-1.5 mt-1">
                          <div className="bg-primary-500/60 h-1.5 rounded-full" style={{ width: `${agent.pct}%` }} />
                        </div>
                      </div>
                      <span className="text-xs text-text-muted">{agent.pct}%</span>
                    </div>
                  ))}
                </CardContent>
              </Card>
              <Card>
                <CardHeader>
                  <div className="flex items-center gap-2">
                    <Globe size={16} className="text-text-secondary" />
                    <CardTitle>Top Referrers</CardTitle>
                  </div>
                </CardHeader>
                <CardContent className="space-y-3">
                  {mockAnalytics.topReferrers.map((ref, i) => (
                    <div key={i} className="flex items-center gap-3">
                      <span className="text-sm text-text-muted w-6">{i + 1}.</span>
                      <div className="flex-1">
                        <div className="flex justify-between text-sm">
                          <span className="text-text-primary">{ref.source}</span>
                          <span className="text-text-secondary">{ref.count.toLocaleString()}</span>
                        </div>
                        <div className="w-full bg-surface-elevated rounded-full h-1.5 mt-1">
                          <div className="bg-secondary-500/60 h-1.5 rounded-full" style={{ width: `${ref.pct}%` }} />
                        </div>
                      </div>
                      <span className="text-xs text-text-muted">{ref.pct}%</span>
                    </div>
                  ))}
                </CardContent>
              </Card>
            </div>

            {/* Privacy Compliance */}
            <Card>
              <CardHeader>
                <div className="flex items-center gap-2">
                  <Shield size={16} className="text-text-secondary" />
                  <CardTitle>Privacy & Compliance</CardTitle>
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="bg-surface-elevated rounded-lg p-4">
                    <p className="text-sm text-text-secondary">Privacy Mode</p>
                    <p className="text-lg font-semibold text-text-primary capitalize">{privacyMode}</p>
                  </div>
                  <div className="bg-surface-elevated rounded-lg p-4">
                    <p className="text-sm text-text-secondary">Data Retention</p>
                    <p className="text-lg font-semibold text-text-primary">{mockAnalytics.dataRetention}</p>
                  </div>
                  <div className="bg-surface-elevated rounded-lg p-4 space-y-2">
                    <p className="text-sm text-text-secondary">Compliance</p>
                    <Badge variant="success">GDPR</Badge>
                    <Badge variant="success" className="ml-1">Kenya DPA</Badge>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Export */}
            <div className="flex justify-end">
              <Button variant="outline" onClick={() => showToast("Analytics export started", "success")}>
                <Download size={16} className="mr-2" /> Export Report
              </Button>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
