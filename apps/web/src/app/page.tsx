"use client";

import React, { useState } from "react";
import { Sidebar } from "@/components/layout/sidebar";
import { Navbar } from "@/components/layout/navbar";
import { cn } from "@/lib/utils";
import { Shield, QrCode, Nfc, Key, Link as LinkIcon } from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";

const quickActions = [
  {
    title: "Generate QR Code",
    description: "Create secure QR codes with expiration and signatures",
    href: "/qr",
    icon: <QrCode size={24} />,
    color: "from-primary-500 to-primary-600",
  },
  {
    title: "Create NFC Payload",
    description: "Generate NFC payloads for physical authentication",
    href: "/nfc",
    icon: <Nfc size={24} />,
    color: "from-secondary-500 to-secondary-600",
  },
  {
    title: "Sign a Link",
    description: "Create time-limited signed links",
    href: "/links",
    icon: <LinkIcon size={24} />,
    color: "from-emerald-500 to-emerald-600",
  },
  {
    title: "Generate Token",
    description: "Create temporary access tokens",
    href: "/tokens",
    icon: <Key size={24} />,
    color: "from-amber-500 to-amber-600",
  },
];

export default function HomePage() {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="flex h-screen overflow-hidden bg-surface">
      <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Navbar onMenuClick={() => setSidebarOpen(true)} />
        <main className="flex-1 overflow-y-auto p-4 lg:p-6">
          <div className="max-w-7xl mx-auto space-y-8">
            {/* Hero Section */}
            <div className="text-center py-12 animate-fade-in">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary-500/10 border border-primary-500/20 text-primary-400 text-sm mb-6">
                <Shield size={14} />
                <span>Privacy-first security toolkit</span>
              </div>
              <h1 className="text-4xl lg:text-5xl font-bold mb-4">
                <span className="gradient-text">VeilPass</span>
              </h1>
              <p className="text-lg text-text-secondary max-w-2xl mx-auto mb-8">
                Generate secure links. Authenticate physical objects. Protect digital access.
              </p>
              <div className="flex items-center justify-center gap-3 flex-wrap">
                <Link href="/qr">
                  <Button size="lg" leftIcon={<QrCode size={18} />}>
                    Generate QR Code
                  </Button>
                </Link>
                <Link href="/tokens">
                  <Button variant="outline" size="lg" leftIcon={<Key size={18} />}>
                    Create Token
                  </Button>
                </Link>
              </div>
            </div>

            {/* Quick Actions */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {quickActions.map((action, index) => (
                <Link key={index} href={action.href}>
                  <Card hover className="p-5 h-full cursor-pointer">
                    <div className="flex items-center gap-3 mb-3">
                      <div
                        className={cn(
                          "w-10 h-10 rounded-lg bg-gradient-to-br flex items-center justify-center text-white",
                          action.color
                        )}
                      >
                        {action.icon}
                      </div>
                    </div>
                    <h3 className="font-semibold text-text-primary mb-1">
                      {action.title}
                    </h3>
                    <p className="text-sm text-text-secondary">
                      {action.description}
                    </p>
                  </Card>
                </Link>
              ))}
            </div>

            {/* Stats */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Card>
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-primary-500/10 flex items-center justify-center">
                    <QrCode size={20} className="text-primary-400" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-text-primary">0</p>
                    <p className="text-xs text-text-secondary">QR Codes Generated</p>
                  </div>
                </div>
              </Card>
              <Card>
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-secondary-500/10 flex items-center justify-center">
                    <LinkIcon size={20} className="text-secondary-400" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-text-primary">0</p>
                    <p className="text-xs text-text-secondary">Links Created</p>
                  </div>
                </div>
              </Card>
              <Card>
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-emerald-500/10 flex items-center justify-center">
                    <Key size={20} className="text-emerald-400" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-text-primary">0</p>
                    <p className="text-xs text-text-secondary">Tokens Issued</p>
                  </div>
                </div>
              </Card>
            </div>

            {/* Recent Activity */}
            <Card>
              <CardHeader>
                <CardTitle>Recent Activity</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-center py-8 text-text-muted">
                  <p>No recent activity yet. Start by generating a QR code or creating a token.</p>
                </div>
              </CardContent>
            </Card>
          </div>
        </main>
      </div>
    </div>
  );
}
