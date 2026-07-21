"use client";

import React, { useState } from "react";
import { Sidebar } from "@/components/layout/sidebar";
import { Navbar } from "@/components/layout/navbar";
import { cn } from "@/lib/utils";
import { Card } from "@/components/ui/card";
import { QrCode, Link as LinkIcon, Key, Shield, Nfc } from "lucide-react";
import NextLink from "next/link";

const stats = [
  { label: "QR Codes Generated", value: "0", icon: <QrCode size={20} />, color: "text-primary-400" },
  { label: "Links Created", value: "0", icon: <LinkIcon size={20} />, color: "text-secondary-400" },
  { label: "Tokens Issued", value: "0", icon: <Key size={20} />, color: "text-emerald-400" },
  { label: "Verifications", value: "0", icon: <Shield size={20} />, color: "text-amber-400" },
];

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

export default function DashboardPage() {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="flex h-screen overflow-hidden bg-surface">
      <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Navbar onMenuClick={() => setSidebarOpen(true)} />
        <main className="flex-1 overflow-y-auto p-4 lg:p-6">
          <div className="max-w-7xl mx-auto space-y-6">
            <div className="animate-fade-in">
              <h1 className="text-2xl font-bold text-text-primary">Dashboard</h1>
              <p className="text-text-secondary mt-1">Overview of your VeilPass activity</p>
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {stats.map((stat, index) => (
                <Card key={index}>
                  <div className="flex items-center gap-3">
                    <div className={cn("w-10 h-10 rounded-lg bg-surface-elevated flex items-center justify-center", stat.color)}>
                      {stat.icon}
                    </div>
                    <div>
                      <p className="text-2xl font-bold text-text-primary">{stat.value}</p>
                      <p className="text-xs text-text-secondary">{stat.label}</p>
                    </div>
                  </div>
                </Card>
              ))}
            </div>

            {/* Quick Actions */}
            <div>
              <h2 className="text-lg font-semibold text-text-primary mb-4">Quick Actions</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {quickActions.map((action, index) => (
                  <NextLink key={index} href={action.href}>
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
                  </NextLink>
                ))}
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
