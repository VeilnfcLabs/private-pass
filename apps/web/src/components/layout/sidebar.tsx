"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import {
  LayoutDashboard,
  QrCode,
  Nfc,
  Link,
  Globe,
  Key,
  Shield,
  BookOpen,
  Settings,
  X,
  Lock,
  Brain,
  Flame,
  BookMarked,
  Eye,
  BarChart3,
} from "lucide-react";

interface NavItem {
  href: string;
  label: string;
  icon: React.ReactNode;
}

const navItems: NavItem[] = [
  { href: "/dashboard", label: "Dashboard", icon: <LayoutDashboard size={18} /> },
  { href: "/qr", label: "QR Generator", icon: <QrCode size={18} /> },
  { href: "/nfc", label: "NFC Generator", icon: <Nfc size={18} /> },
  { href: "/links", label: "Signed Links", icon: <Link size={18} /> },
  { href: "/signed-urls", label: "Signed URLs", icon: <Globe size={18} /> },
  { href: "/tokens", label: "Temporary Tokens", icon: <Key size={18} /> },
  { href: "/sd-jwt", label: "SD-JWT", icon: <Lock size={18} /> },
  { href: "/ephemeral", label: "Ephemeral", icon: <Flame size={18} /> },
  { href: "/encrypted", label: "Encrypted", icon: <Lock size={18} /> },
  { href: "/zkp", label: "ZKP Auth", icon: <Brain size={18} /> },
  { href: "/registry", label: "Trust Registry", icon: <BookMarked size={18} /> },
  { href: "/analytics", label: "Analytics", icon: <BarChart3 size={18} /> },
  { href: "/verify", label: "Verification", icon: <Shield size={18} /> },
  { href: "/api-keys", label: "API Keys", icon: <Key size={18} /> },
  { href: "/settings", label: "Settings", icon: <Settings size={18} /> },
];

interface SidebarProps {
  open: boolean;
  onClose: () => void;
}

export function Sidebar({ open, onClose }: SidebarProps) {
  const pathname = usePathname();

  return (
    <>
      {/* Mobile overlay */}
      {open && (
        <div
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={onClose}
        />
      )}
      <aside
        className={cn(
          "fixed lg:static inset-y-0 left-0 z-50 w-64 bg-surface border-r border-border transform transition-transform duration-300 ease-in-out lg:transform-none overflow-y-auto",
          open ? "translate-x-0" : "-translate-x-full lg:translate-x-0"
        )}
      >
        <div className="p-4 border-b border-border">
          <Link href="/dashboard" className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary-500 to-secondary-500 flex items-center justify-center">
              <Shield size={16} className="text-white" />
            </div>
            <span className="text-lg font-bold gradient-text">VeilPass</span>
          </Link>
        </div>
        <nav className="p-3 space-y-1">
          {navItems.map((item) => {
            const isActive = pathname === item.href || pathname.startsWith(item.href + "/");
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200",
                  isActive
                    ? "bg-primary-500/10 text-primary-400 border border-primary-500/20"
                    : "text-text-secondary hover:bg-surface-elevated hover:text-text-primary"
                )}
              >
                {item.icon}
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>
      </div>
    </aside>
  );
}
