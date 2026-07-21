"use client";

import React, { useState } from "react";
import { Sidebar } from "@/components/layout/sidebar";
import { Navbar } from "@/components/layout/navbar";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { Select } from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { showToast } from "@/components/ui/toast";
import { Shield, CheckCircle, XCircle, AlertTriangle } from "lucide-react";

export default function VerifyPage() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [input, setInput] = useState("");
  const [type, setType] = useState("token");
  const [result, setResult] = useState<{
    valid: boolean;
    expired: boolean;
    issuer?: string;
    claims?: Record<string, unknown>;
    signatureValid: boolean;
  } | null>(null);

  const handleVerify = () => {
    if (!input.trim()) {
      showToast("Please enter a token, link, or URL to verify", "error");
      return;
    }
    // Simulated verification
    setResult({
      valid: true,
      expired: false,
      issuer: "VeilPass",
      claims: { sub: "user-123", aud: "api.veilpass.dev" },
      signatureValid: true,
    });
    showToast("Verification complete", "success");
  };

  return (
    <div className="flex h-screen overflow-hidden bg-surface">
      <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Navbar onMenuClick={() => setSidebarOpen(true)} />
        <main className="flex-1 overflow-y-auto p-4 lg:p-6">
          <div className="max-w-7xl mx-auto space-y-6">
            <div className="animate-fade-in">
              <h1 className="text-2xl font-bold text-text-primary">Verification</h1>
              <p className="text-text-secondary mt-1">Verify tokens, signed links, and signed URLs</p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Input Form */}
              <Card>
                <CardHeader>
                  <CardTitle>Verify</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <Textarea
                    label="Token / Link / URL"
                    placeholder="Paste the token, signed link, or signed URL to verify..."
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    rows={4}
                  />
                  <Select
                    label="Type"
                    value={type}
                    onChange={(e) => setType(e.target.value)}
                    options={[
                      { value: "token", label: "Token" },
                      { value: "signed-link", label: "Signed Link" },
                      { value: "signed-url", label: "Signed URL" },
                    ]}
                  />
                  <Button className="w-full" size="lg" onClick={handleVerify}>
                    Verify
                  </Button>
                </CardContent>
              </Card>

              {/* Result */}
              <Card>
                <CardHeader>
                  <CardTitle>Verification Result</CardTitle>
                </CardHeader>
                <CardContent>
                  {result ? (
                    <div className="space-y-4 animate-fade-in">
                      <div className="flex items-center gap-3">
                        {result.valid ? (
                          <Badge variant="success">Valid</Badge>
                        ) : (
                          <Badge variant="error">Invalid</Badge>
                        )}
                        {result.expired ? (
                          <Badge variant="warning">Expired</Badge>
                        ) : (
                          <Badge variant="success">Not Expired</Badge>
                        )}
                        {result.signatureValid ? (
                          <Badge variant="success">Signature Valid</Badge>
                        ) : (
                          <Badge variant="error">Signature Invalid</Badge>
                        )}
                      </div>
                      {result.issuer && (
                        <div className="flex items-center gap-2">
                          <span className="text-sm text-text-secondary">Issuer:</span>
                          <span className="text-sm text-text-primary font-medium">{result.issuer}</span>
                        </div>
                      )}
                      {result.claims && (
                        <div>
                          <span className="text-sm text-text-secondary block mb-1">Claims:</span>
                          <pre className="bg-surface-elevated rounded-lg p-3 text-xs font-mono text-text-primary overflow-x-auto">
                            {JSON.stringify(result.claims, null, 2)}
                          </pre>
                        </div>
                      )}
                    </>
                  ) : (
                    <div className="text-center py-12 text-text-muted">
                      <Shield size={48} className="mx-auto mb-3 opacity-30" />
                      <p>Verify a token or link to see the result</p>
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
