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
import { cn } from "@/lib/utils";
import { showToast } from "@/components/ui/toast";
import { copyToClipboard } from "@/lib/utils";
import { Key, Copy, RefreshCw, Code } from "lucide-react";

const expirationPresets = [
  { value: "5min", label: "5 Min" },
  { value: "10min", label: "10 Min" },
  { value: "30min", label: "30 Min" },
  { value: "1h", label: "1 Hour" },
  { value: "custom", label: "Custom" },
];

export default function TokensPage() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [subject, setSubject] = useState("");
  const [audience, setAudience] = useState("");
  const [issuer, setIssuer] = useState("VeilPass");
  const [expirationPreset, setExpirationPreset] = useState("1h");
  const [customExpiration, setCustomExpiration] = useState("");
  const [customClaims, setCustomClaims] = useState("{}");
  const [generatedToken, setGeneratedToken] = useState<string | null>(null);
  const [decodedToken, setDecodedToken] = useState<{ header: string; payload: string; signature: string } | null>(null);

  const handleGenerate = () => {
    if (!subject.trim()) {
      showToast("Please enter a subject", "error");
      return;
    }
    const token = `eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCJ9.${btoa(JSON.stringify({ sub: subject, aud: audience, iss: issuer, exp: expirationPreset }))}.dummy_signature`;
    setGeneratedToken(token);
    setDecodedToken({
      header: JSON.stringify({ alg: "ES256", typ: "JWT" }, null, 2),
      payload: JSON.stringify({ sub: subject, aud: audience, iss: issuer, exp: expirationPreset }, null, 2),
      signature: "dummy_signature",
    });
    showToast("Token generated successfully", "success");
  };

  return (
    <div className="flex h-screen overflow-hidden bg-surface">
      <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Navbar onMenuClick={() => setSidebarOpen(true)} />
        <main className="flex-1 overflow-y-auto p-4 lg:p-6">
          <div className="max-w-7xl mx-auto space-y-6">
            <div className="animate-fade-in">
              <h1 className="text-2xl font-bold text-text-primary">Temporary Tokens</h1>
              <p className="text-text-secondary mt-1">Create time-limited JWT tokens for temporary access</p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Input Form */}
              <Card>
                <CardHeader>
                  <CardTitle>Configuration</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <Input
                    label="Subject"
                    placeholder="user-123 or session-id"
                    value={subject}
                    onChange={(e) => setSubject(e.target.value)}
                  />
                  <Input
                    label="Audience"
                    placeholder="api.veilpass.dev"
                    value={audience}
                    onChange={(e) => setAudience(e.target.value)}
                  />
                  <Input
                    label="Issuer"
                    value={issuer}
                    onChange={(e) => setIssuer(e.target.value)}
                    placeholder="VeilPass"
                  />
                  <div>
                    <label className="text-sm text-text-secondary mb-2 block">Expiration</label>
                    <div className="flex flex-wrap gap-2">
                      {expirationPresets.map((preset) => (
                        <button
                          key={preset.value}
                          onClick={() => setExpirationPreset(preset.value)}
                          className={cn(
                            "px-3 py-1.5 rounded-lg text-xs font-medium border transition-all",
                            expirationPreset === preset.value
                              ? "border-primary-500 bg-primary-500/10 text-primary-400"
                              : "border-border text-text-secondary hover:border-primary-500/50"
                          )}
                        >
                          {preset.label}
                        </button>
                      ))}
                    </div>
                  )}
                  {expirationPreset === "custom" && (
                    <Input
                      type="datetime-local"
                      label="Custom Expiration"
                      value={customExpiration}
                      onChange={(e) => setCustomExpiration(e.target.value)}
                    />
                  )}
                  <Textarea
                    label="Custom Claims (JSON)"
                    placeholder='{"scope": "read:files"}'
                    value={customClaims}
                    onChange={(e) => setCustomClaims(e.target.value)}
                    rows={3}
                  />
                  <Button className="w-full" size="lg" onClick={handleGenerate}>
                    Generate Token
                  </Button>
                </CardContent>
              </Card>

              {/* Output */}
              <Card>
                <CardHeader>
                  <CardTitle>Generated Token</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  {generatedToken ? (
                    <>
                      <div className="bg-surface-elevated rounded-lg p-4 font-mono text-xs text-text-primary break-all">
                        {generatedToken}
                      </div>
                      <Tabs
                        tabs={[
                          {
                            id: "header",
                            label: "Header",
                            content: (
                              <pre className="bg-surface-elevated rounded-lg p-4 text-xs font-mono text-text-primary overflow-x-auto">
                                {decodedToken?.header || "{}"}
                              </pre>
                            ),
                          },
                          {
                            id: "payload",
                            label: "Payload",
                            content: (
                              <pre className="bg-surface-elevated rounded-lg p-4 text-xs font-mono text-text-primary overflow-x-auto">
                                {decodedToken?.payload || "{}"}
                              </pre>
                            ),
                          },
                          {
                            id: "signature",
                            label: "Signature",
                            content: (
                              <div className="bg-surface-elevated rounded-lg p-4 font-mono text-xs text-text-primary break-all">
                                {decodedToken?.signature || "N/A"}
                              </div>
                            ),
                          },
                        ]}
                      />
                      <div className="flex gap-2">
                        <Button variant="outline" leftIcon={<Copy size={16} />}>
                          Copy Token
                        </Button>
                        <Button variant="ghost" leftIcon={<RefreshCw size={16} />}>
                          Regenerate
                        </Button>
                      </div>
                    </>
                  ) : (
                    <div className="text-center py-12 text-text-muted">
                      <Key size={48} className="mx-auto mb-3 opacity-30" />
                      <p>Generate a token to see the result</p>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
