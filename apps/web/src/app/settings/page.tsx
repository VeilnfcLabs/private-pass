"use client";

import React, { useState } from "react";
import { Sidebar } from "@/components/layout/sidebar";
import { Navbar } from "@/components/layout/navbar";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { useThemeStore } from "@/lib/stores/themeStore";
import { showToast } from "@/components/ui/toast";
import { Sun, Moon, Download, Upload, Save } from "lucide-react";

export default function SettingsPage() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { theme, setTheme } = useThemeStore();
  const [defaultAlgorithm, setDefaultAlgorithm] = useState("Ed25519");
  const [defaultTtl, setDefaultTtl] = useState("3600");
  const [apiEndpoint, setApiEndpoint] = useState("http://localhost:8000");

  const handleSave = () => {
    showToast("Settings saved", "success");
  };

  return (
    <div className="flex h-screen overflow-hidden bg-surface">
      <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Navbar onMenuClick={() => setSidebarOpen(true)} />
        <main className="flex-1 overflow-y-auto p-4 lg:p-6">
          <div className="max-w-4xl mx-auto space-y-6">
            <div className="animate-fade-in">
              <h1 className="text-2xl font-bold text-text-primary">Settings</h1>
              <p className="text-text-secondary mt-1">Configure your VeilPass preferences</p>
            </div>

            {/* Theme */}
            <Card>
              <CardHeader>
                <CardTitle>Appearance</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center justify-between p-4 rounded-lg bg-surface-elevated border border-border">
                  <div>
                    <p className="text-sm font-medium text-text-primary">Theme</p>
                    <p className="text-xs text-text-secondary">Toggle between dark and light mode</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button
                      variant={theme === "dark" ? "primary" : "outline"}
                      size="sm"
                      onClick={() => setTheme("dark")}
                    >
                      <Moon size={14} className="mr-1" />
                      Dark
                    </Button>
                    <Button
                      variant={theme === "light" ? "primary" : "outline"}
                      size="sm"
                      onClick={() => setTheme("light")}
                    >
                      <Sun size={14} className="mr-1" />
                      Light
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Defaults */}
            <Card>
              <CardHeader>
                <CardTitle>Defaults</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <Select
                  label="Default Algorithm"
                  value={defaultAlgorithm}
                  onChange={(e) => setDefaultAlgorithm(e.target.value)}
                  options={[
                    { value: "Ed25519", label: "Ed25519" },
                    { value: "HMAC", label: "HMAC" },
                  ]}
                />
                <Input
                  label="Default Token TTL (seconds)"
                  type="number"
                  value={defaultTtl}
                  onChange={(e) => setDefaultTtl(e.target.value)}
                  min={60}
                />
                <Input
                  label="API Endpoint"
                  value={apiEndpoint}
                  onChange={(e) => setApiEndpoint(e.target.value)}
                  placeholder="http://localhost:8000"
                />
              </CardContent>
            </Card>

            {/* Key Management */}
            <Card>
              <CardHeader>
                <CardTitle>Key Management</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <p className="text-sm text-text-secondary">
                  Export or import your signing keys for backup or migration.
                </p>
                <div className="flex gap-3">
                  <Button variant="outline" leftIcon={<Download size={16} />}>
                    Export Keys
                  </Button>
                  <Button variant="outline" leftIcon={<Upload size={16} />}>
                    Import Keys
                  </Button>
                </div>
              </CardContent>
            </Card>

            {/* Save */}
            <div className="flex justify-end">
              <Button size="lg" onClick={handleSave} leftIcon={<Save size={16} />}>
                Save All Settings
              </Button>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
