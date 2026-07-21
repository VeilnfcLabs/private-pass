"use client";

import React, { useState } from "react";
import { Sidebar } from "@/components/layout/sidebar";
import { Navbar } from "@/components/layout/navbar";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Dialog } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { showToast } from "@/components/ui/toast";
import { copyToClipboard, maskString, formatDate } from "@/lib/utils";
import { Key, Copy, Trash2, Plus, Eye, EyeOff } from "lucide-react";

interface ApiKey {
  id: string;
  name: string;
  key: string;
  createdAt: string;
  lastUsed: string | null;
  revoked: boolean;
}

export default function ApiKeysPage() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [keys, setKeys] = useState<ApiKey[]>([]);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [newKeyName, setNewKeyName] = useState("");
  const [newKeyValue, setNewKeyValue] = useState<string | null>(null);

  const handleCreateKey = () => {
    if (!newKeyName.trim()) {
      showToast("Please enter a key name", "error");
      return;
    }
    const key = `vp_${Math.random().toString(36).substring(2, 34)}`;
    setNewKeyValue(key);
    setKeys([...keys, { id: Math.random().toString(36).substring(2, 10), name: newKeyName, key, createdAt: new Date().toISOString(), lastUsed: null, revoked: false }]);
    showToast("API key created", "success");
  };

  const handleRevoke = (id: string) => {
    setKeys(keys.map(k => k.id === id ? { ...k, revoked: true } : k));
    showToast("API key revoked", "success");
  };

  return (
    <div className="flex h-screen overflow-hidden bg-surface">
      <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Navbar onMenuClick={() => setSidebarOpen(true)} />
        <main className="flex-1 overflow-y-auto p-4 lg:p-6">
          <div className="max-w-4xl mx-auto space-y-6">
            <div className="animate-fade-in flex items-center justify-between">
              <div>
                <h1 className="text-2xl font-bold text-text-primary">API Keys</h1>
                <p className="text-text-secondary mt-1">Manage your API keys for programmatic access</p>
              </div>
              <Button leftIcon={<Plus size={16} />} onClick={() => setShowCreateDialog(true)}>
                Create Key
              </Button>
            </div>

            {/* Keys List */}
            <Card>
              <CardHeader>
                <CardTitle>Your API Keys</CardTitle>
              </CardHeader>
              <CardContent>
                {keys.length === 0 ? (
                  <div className="text-center py-12 text-text-muted">
                    <Key size={48} className="mx-auto mb-3 opacity-30" />
                    <p>No API keys yet. Create one to get started.</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {keys.map((apiKey) => (
                      <div
                        key={apiKey.id}
                        className="flex items-center justify-between p-4 rounded-lg bg-surface-elevated border border-border"
                      >
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <span className="font-medium text-text-primary">{apiKey.name}</span>
                            {apiKey.revoked && <Badge variant="error">Revoked</Badge>}
                          </div>
                          <p className="text-sm font-mono text-text-muted">
                            {maskString(apiKey.key)}
                          </p>
                          <p className="text-xs text-text-muted mt-1">
                            Created {formatDate(apiKey.createdAt)}
                          </p>
                        </div>
                        <div className="flex items-center gap-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => {
                              copyToClipboard(apiKey.key);
                              showToast("API key copied", "success");
                            }}
                          >
                            <Copy size={14} />
                          </Button>
                          {!apiKey.revoked && (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => {
                                setKeys(keys.map(k => k.id === apiKey.id ? { ...k, revoked: true } : k));
                                showToast("API key revoked", "success");
                              }}
                            >
                              <Trash2 size={14} className="text-red-400" />
                            </Button>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </main>
      </div>
    </div>
  );
}
