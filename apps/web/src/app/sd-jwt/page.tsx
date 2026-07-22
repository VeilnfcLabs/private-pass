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
import { Eye, EyeOff, Lock, Unlock, CheckCircle, Copy, RefreshCw } from "lucide-react";

export default function SdJwtPage() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [claims, setClaims] = useState('{"sub": "user_42", "email": "user@example.com", "role": "admin", "department": "engineering"}');
  const [issuer, setIssuer] = useState("VeilPass");
  const [sdJwt, setSdJwt] = useState<string | null>(null);
  const [disclosures, setDisclosures] = useState<string[]>([]);
  const [revealedClaims, setRevealedClaims] = useState<Record<string, boolean>>({});
  const [presentationResult, setPresentationResult] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState("generate");

  const handleGenerate = async () => {
    try {
      const parsed = JSON.parse(claims);
      const keys = Object.keys(parsed);
      const discs = keys.map((k) => `${k}:${btoa(parsed[k])}`);
      setDisclosures(discs);
      const initial: Record<string, boolean> = {};
      keys.forEach((k) => { initial[k] = true; });
      setRevealedClaims(initial);
      const header = btoa(JSON.stringify({ alg: "SD-JWT", typ: "sd+jwt", iss: issuer }));
      const payload = btoa(JSON.stringify({ _sd: discs.map((d) => btoa(d)), iss: issuer, iat: Math.floor(Date.now() / 1000) }));
      setSdJwt(`${header}.${payload}`);
      setPresentationResult(null);
      showToast("SD-JWT generated successfully", "success");
    } catch {
      showToast("Invalid JSON in claims", "error");
    }
  };

  const handlePresent = () => {
    if (!sdJwt) return;
    const selected = disclosures.filter((_, i) => revealedClaims[Object.keys(JSON.parse(claims))[i]]);
    const presentPayload = btoa(JSON.stringify({ _sd: selected.map((d) => btoa(d)), iss: issuer }));
    setPresentationResult(`sd_jwt_present_${presentPayload}`);
    showToast("Presentation created with selected disclosures", "success");
  };

  const toggleClaim = (key: string) => {
    setRevealedClaims((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const getSelectedKeys = () => Object.keys(revealedClaims).filter((k) => revealedClaims[k]);

  return (
    <div className="flex h-screen overflow-hidden bg-surface">
      <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Navbar onMenuClick={() => setSidebarOpen(true)} />
        <main className="flex-1 overflow-y-auto p-4 lg:p-6">
          <div className="max-w-7xl mx-auto space-y-6">
            <div className="animate-fade-in">
              <h1 className="text-2xl font-bold text-text-primary">Selective Disclosure (SD-JWT)</h1>
              <p className="text-text-secondary mt-1">Issue and verify JWTs with selective claim disclosure</p>
            </div>

            <Tabs
              tabs={[
                {
                  id: "generate",
                  label: "Generate",
                  content: (
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
                      <Card>
                        <CardHeader>
                          <CardTitle>Claims Configuration</CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-4">
                          <Input label="Issuer" value={issuer} onChange={(e) => setIssuer(e.target.value)} placeholder="VeilPass" />
                          <Textarea label="Claims (JSON)" value={claims} onChange={(e) => setClaims(e.target.value)} rows={6} />
                          <Button className="w-full" size="lg" onClick={handleGenerate}>
                            <Lock size={16} className="mr-2" /> Generate SD-JWT
                          </Button>
                        </CardContent>
                      </Card>
                      <Card>
                        <CardHeader>
                          <CardTitle>Generated SD-JWT</CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-4">
                          {sdJwt ? (
                            <>
                              <div className="bg-surface-elevated rounded-lg p-4 font-mono text-xs text-text-primary break-all">{sdJwt}</div>
                              <Button variant="outline" onClick={() => { copyToClipboard(sdJwt); showToast("Copied to clipboard", "success"); }}>
                                <Copy size={16} className="mr-2" /> Copy SD-JWT
                              </Button>
                              <div className="space-y-2">
                                {disclosures.map((d, i) => {
                                  const key = Object.keys(JSON.parse(claims))[i];
                                  const isRevealed = revealedClaims[key];
                                  return (
                                    <div key={key} className="flex items-center justify-between bg-surface-elevated rounded-lg p-3">
                                      <div className="flex items-center gap-2">
                                        {isRevealed ? <Unlock size={16} className="text-green-400" /> : <EyeOff size={16} className="text-text-muted" />}
                                        <span className="text-sm font-mono text-text-primary">{key}</span>
                                      </div>
                                      <div className="flex items-center gap-2">
                                        <Badge variant={isRevealed ? "success" : "ghost"}>{isRevealed ? "Revealed" : "Hidden"}</Badge>
                                        <Switch checked={isRevealed} onChange={() => toggleClaim(key)} />
                                      </div>
                                    </div>
                                  );
                                })}
                              </div>
                              <Button className="w-full" onClick={handlePresent}>
                                <Eye size={16} className="mr-2" /> Present Selected Claims ({getSelectedKeys().length}/{disclosures.length})
                              </Button>
                            </>
                          ) : (
                            <div className="text-center py-12 text-text-muted">
                              <Lock size={48} className="mx-auto mb-3 opacity-30" />
                              <p>Configure claims and generate an SD-JWT</p>
                            </div>
                          )}
                        </CardContent>
                      </Card>
                    </div>
                  ),
                },
                {
                  id: "presentation",
                  label: "Presentation",
                  content: (
                    <div className="mt-6 space-y-6">
                      {presentationResult ? (
                        <Card>
                          <CardHeader>
                            <CardTitle>Presentation Result</CardTitle>
                          </CardHeader>
                          <CardContent className="space-y-4">
                            <div className="bg-surface-elevated rounded-lg p-4 font-mono text-xs text-text-primary break-all">{presentationResult}</div>
                            <p className="text-sm text-text-secondary">
                              <CheckCircle size={14} className="inline mr-1 text-green-400" />
                              Claims disclosed: {getSelectedKeys().join(", ") || "none"}
                            </p>
                            <Button variant="outline" onClick={() => { copyToClipboard(presentationResult); showToast("Copied presentation", "success"); }}>
                              <Copy size={16} className="mr-2" /> Copy Presentation
                            </Button>
                          </CardContent>
                        </Card>
                      ) : (
                        <Card>
                          <CardContent className="text-center py-12 text-text-muted">
                            <EyeOff size={48} className="mx-auto mb-3 opacity-30" />
                            <p>Generate an SD-JWT first and select which claims to reveal</p>
                          </CardContent>
                        </Card>
                      )}
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
