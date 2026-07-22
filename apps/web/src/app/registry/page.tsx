"use client";

import React, { useState } from "react";
import { Sidebar } from "@/components/layout/sidebar";
import { Navbar } from "@/components/layout/navbar";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { showToast } from "@/components/ui/toast";
import { copyToClipboard } from "@/lib/utils";
import { BookOpen, UserPlus, Users, ShieldCheck, Copy, Search } from "lucide-react";

export default function RegistryPage() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [did, setDid] = useState("");
  const [issuerName, setIssuerName] = useState("");
  const [publicKey, setPublicKey] = useState("");
  const [registrations, setRegistrations] = useState<Array<{ did: string; name: string; key: string; ts: string }>>([]);
  const [lookupDid, setLookupDid] = useState("");
  const [lookupResult, setLookupResult] = useState<{ did: string; name: string; key: string; ts: string } | null>(null);
  const [verifyCredential, setVerifyCredential] = useState("");
  const [verifyIssuer, setVerifyIssuer] = useState("");
  const [credVerifyResult, setCredVerifyResult] = useState<boolean | null>(null);

  const handleRegister = () => {
    if (!did.trim() || !issuerName.trim() || !publicKey.trim()) { showToast("Fill all fields", "error"); return; }
    const entry = { did, name: issuerName, key: publicKey, ts: new Date().toISOString() };
    setRegistrations((prev) => [entry, ...prev]);
    setDid(""); setIssuerName(""); setPublicKey("");
    showToast("Issuer registered in trust registry", "success");
  };

  const handleLookup = () => {
    if (!lookupDid.trim()) { showToast("Enter a DID to look up", "error"); return; }
    const found = registrations.find((r) => r.did === lookupDid);
    if (found) { setLookupResult(found); showToast("Issuer found", "success"); }
    else { setLookupResult(null); showToast("Issuer not found in registry", "error"); }
  };

  const handleVerifyCred = () => {
    if (!verifyCredential.trim() || !verifyIssuer.trim()) { showToast("Fill all fields", "error"); return; }
    const issuerExists = registrations.some((r) => r.did === verifyIssuer);
    setCredVerifyResult(issuerExists);
    showToast(issuerExists ? "Credential issuer is verified" : "Issuer not in trust registry", issuerExists ? "success" : "error");
  };

  return (
    <div className="flex h-screen overflow-hidden bg-surface">
      <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Navbar onMenuClick={() => setSidebarOpen(true)} />
        <main className="flex-1 overflow-y-auto p-4 lg:p-6">
          <div className="max-w-7xl mx-auto space-y-6">
            <div className="animate-fade-in">
              <h1 className="text-2xl font-bold text-text-primary">Trust Registry</h1>
              <p className="text-text-secondary mt-1">Decentralized issuer registry with DID verification</p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card>
                <CardHeader><CardTitle>Register Issuer</CardTitle></CardHeader>
                <CardContent className="space-y-4">
                  <Input label="DID" value={did} onChange={(e) => setDid(e.target.value)} placeholder="did:veilpass:abc123" />
                  <Input label="Issuer Name" value={issuerName} onChange={(e) => setIssuerName(e.target.value)} placeholder="My Organization" />
                  <Textarea label="Public Key" value={publicKey} onChange={(e) => setPublicKey(e.target.value)} placeholder="-----BEGIN PUBLIC KEY-----" rows={3} />
                  <Button className="w-full" onClick={handleRegister}>
                    <UserPlus size={16} className="mr-2" /> Register Issuer
                  </Button>
                </CardContent>
              </Card>

              <div className="space-y-6">
                <Card>
                  <CardHeader><CardTitle>Lookup Issuer</CardTitle></CardHeader>
                  <CardContent className="space-y-4">
                    <div className="flex gap-2">
                      <Input label="DID" value={lookupDid} onChange={(e) => setLookupDid(e.target.value)} placeholder="did:veilpass:..." />
                      <div className="pt-6"><Button onClick={handleLookup}><Search size={16} /></Button></div>
                    </div>
                    {lookupResult && (
                      <div className="bg-surface-elevated rounded-lg p-3 space-y-1">
                        <p className="text-sm font-semibold text-text-primary">{lookupResult.name}</p>
                        <p className="text-xs text-text-secondary">{lookupResult.did}</p>
                        <p className="text-xs text-text-muted font-mono break-all">{lookupResult.key.slice(0, 48)}...</p>
                        <p className="text-xs text-text-muted">Registered: {new Date(lookupResult.ts).toLocaleString()}</p>
                      </div>
                    )}
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader><CardTitle>Verify Credential Issuer</CardTitle></CardHeader>
                  <CardContent className="space-y-4">
                    <Input label="Credential / Token" value={verifyCredential} onChange={(e) => setVerifyCredential(e.target.value)} placeholder="Credential data..." />
                    <Input label="Issuer DID" value={verifyIssuer} onChange={(e) => setVerifyIssuer(e.target.value)} placeholder="did:veilpass:..." />
                    <Button className="w-full" variant="outline" onClick={handleVerifyCred}>
                      <ShieldCheck size={16} className="mr-2" /> Verify Issuer
                    </Button>
                    {credVerifyResult !== null && (
                      <Badge variant={credVerifyResult ? "success" : "error"} className="w-full justify-center py-2">
                        {credVerifyResult ? "Verified Issuer" : "Unknown Issuer"}
                      </Badge>
                    )}
                  </CardContent>
                </Card>
              </div>
            </div>

            {registrations.length > 0 && (
              <Card>
                <CardHeader><CardTitle>Registered Issuers ({registrations.length})</CardTitle></CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {registrations.map((r, i) => (
                      <div key={i} className="flex items-center justify-between bg-surface-elevated rounded-lg p-3">
                        <div>
                          <p className="text-sm font-semibold text-text-primary">{r.name}</p>
                          <p className="text-xs text-text-secondary font-mono">{r.did}</p>
                        </div>
                        <div className="text-right text-xs text-text-muted">
                          <p>{new Date(r.ts).toLocaleDateString()}</p>
                          <Button variant="ghost" size="sm" onClick={() => { copyToClipboard(r.did); showToast("DID copied", "success"); }}>
                            <Copy size={12} />
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        </main>
      </div>
    </div>
  );
}
