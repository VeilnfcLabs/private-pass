"use client";

import React, { useState } from "react";
import { Sidebar } from "@/components/layout/sidebar";
import { Navbar } from "@/components/layout/navbar";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs } from "@/components/ui/tabs";
import { Switch } from "@/components/ui/switch";
import { showToast } from "@/components/ui/toast";
import { copyToClipboard, cn } from "@/lib/utils";
import { Timer, Zap, Shield, Copy, Clock, Flame } from "lucide-react";

const ttlPresets = [
  { value: 300, label: "5 Min", color: "text-green-400" },
  { value: 600, label: "10 Min", color: "text-emerald-400" },
  { value: 1800, label: "30 Min", color: "text-yellow-400" },
  { value: 3600, label: "1 Hour", color: "text-orange-400" },
  { value: 86400, label: "24 Hours", color: "text-red-400" },
];

export default function EphemeralPage() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [content, setContent] = useState("");
  const [selectedTtl, setSelectedTtl] = useState(600);
  const [oneTime, setOneTime] = useState(true);
  const [generatedToken, setGeneratedToken] = useState<string | null>(null);
  const [verifyToken, setVerifyToken] = useState("");
  const [verifyResult, setVerifyResult] = useState<boolean | null>(null);

  const handleGenerate = () => {
    if (!content.trim()) { showToast("Enter content for the credential", "error"); return; }
    const prefix = oneTime ? "ep_ot_" : "ep_";
    const token = `${prefix}${btoa(content)}_${selectedTtl}s_${Date.now()}`;
    setGeneratedToken(token);
    showToast(`Ephemeral credential created (${selectedTtl}s TTL)`, "success");
  };

  const handleVerify = () => {
    if (!verifyToken.trim()) { showToast("Enter an ephemeral token", "error"); return; }
    const isValid = verifyToken.startsWith("ep_") && verifyToken.length > 10;
    setVerifyResult(isValid);
    showToast(isValid ? "Token is valid" : "Invalid or expired token", isValid ? "success" : "error");
  };

  return (
    <div className="flex h-screen overflow-hidden bg-surface">
      <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Navbar onMenuClick={() => setSidebarOpen(true)} />
        <main className="flex-1 overflow-y-auto p-4 lg:p-6">
          <div className="max-w-7xl mx-auto space-y-6">
            <div className="animate-fade-in">
              <div className="flex items-center gap-2">
                <Flame size={24} className="text-orange-400" />
                <h1 className="text-2xl font-bold text-text-primary">Ephemeral Credentials</h1>
              </div>
              <p className="text-text-secondary mt-1">Self-destructing credentials with sub-minute to 24-hour TTLs</p>
            </div>

            <Tabs
              tabs={[
                {
                  id: "create",
                  label: "Create",
                  content: (
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
                      <Card>
                        <CardHeader><CardTitle>Credential Configuration</CardTitle></CardHeader>
                        <CardContent className="space-y-4">
                          <Textarea label="Content" value={content} onChange={(e) => setContent(e.target.value)} placeholder="Credential data to protect" rows={3} />
                          <div>
                            <label className="text-sm text-text-secondary mb-2 block">Time-to-Live</label>
                            <div className="flex flex-wrap gap-2">
                              {ttlPresets.map((preset) => (
                                <button key={preset.value} onClick={() => setSelectedTtl(preset.value)}
                                  className={cn("px-3 py-1.5 rounded-lg text-xs font-medium border transition-all", selectedTtl === preset.value ? "border-primary-500 bg-primary-500/10 text-primary-400" : "border-border text-text-secondary hover:border-primary-500/50")}>
                                  {preset.label}
                                </button>
                              ))}
                            </div>
                          </div>
                          <div className="flex items-center justify-between bg-surface-elevated rounded-lg p-3">
                            <div className="flex items-center gap-2">
                              <Zap size={16} className="text-amber-400" />
                              <span className="text-sm text-text-primary">One-time use (auto-destruct)</span>
                            </div>
                            <Switch checked={oneTime} onChange={() => setOneTime(!oneTime)} />
                          </div>
                          <Button className="w-full" size="lg" onClick={handleGenerate}>
                            <Timer size={16} className="mr-2" /> Create Ephemeral Credential
                          </Button>
                        </CardContent>
                      </Card>
                      <Card>
                        <CardHeader><CardTitle>Generated Credential</CardTitle></CardHeader>
                        <CardContent className="space-y-4">
                          {generatedToken ? (
                            <>
                              <div className="bg-surface-elevated rounded-lg p-4 font-mono text-xs text-text-primary break-all">{generatedToken}</div>
                              <div className="flex gap-2">
                                <Button variant="outline" onClick={() => { copyToClipboard(generatedToken); showToast("Copied", "success"); }}>
                                  <Copy size={16} className="mr-2" /> Copy
                                </Button>
                                <Badge variant="warning"><Clock size={12} className="mr-1" /> Expires in {selectedTtl}s</Badge>
                                {oneTime && <Badge variant="error">One-Time</Badge>}
                              </div>
                            </>
                          ) : (
                            <div className="text-center py-12 text-text-muted">
                              <Flame size={48} className="mx-auto mb-3 opacity-30" />
                              <p>Configure and create an ephemeral credential</p>
                            </div>
                          )}
                        </CardContent>
                      </Card>
                    </div>
                  ),
                },
                {
                  id: "verify",
                  label: "Verify",
                  content: (
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
                      <Card>
                        <CardHeader><CardTitle>Verify Credential</CardTitle></CardHeader>
                        <CardContent className="space-y-4">
                          <Input label="Ephemeral Token" value={verifyToken} onChange={(e) => setVerifyToken(e.target.value)} placeholder="ep_ot_..." />
                          <Button className="w-full" onClick={handleVerify}><Shield size={16} className="mr-2" /> Verify</Button>
                        </CardContent>
                      </Card>
                      <Card>
                        <CardHeader><CardTitle>Result</CardTitle></CardHeader>
                        <CardContent>
                          {verifyResult !== null ? (
                            <div className={`text-center py-8 ${verifyResult ? "text-green-400" : "text-red-400"}`}>
                              <Shield size={48} className="mx-auto mb-3" />
                              <p className="text-lg font-semibold">{verifyResult ? "Valid Credential" : "Invalid / Expired"}</p>
                            </div>
                          ) : (
                            <div className="text-center py-12 text-text-muted">
                              <Shield size={48} className="mx-auto mb-3 opacity-30" />
                              <p>Enter a token to verify</p>
                            </div>
                          )}
                        </CardContent>
                      </Card>
                    </div>
                  ),
                },
              ]}
            />
          </div>
        </main>
      </div>
    </div>
  );
}
