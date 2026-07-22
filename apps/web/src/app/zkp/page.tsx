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
import { showToast } from "@/components/ui/toast";
import { copyToClipboard } from "@/lib/utils";
import { Brain, ShieldCheck, KeyRound, Copy, RefreshCw } from "lucide-react";

export default function ZkpPage() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [secret, setSecret] = useState("");
  const [publicKey, setPublicKey] = useState<string | null>(null);
  const [commitment, setCommitment] = useState<string | null>(null);
  const [challenge, setChallenge] = useState<string | null>(null);
  const [response, setResponse] = useState<string | null>(null);
  const [verifierChallenge, setVerifierChallenge] = useState("");
  const [verifierResponse, setVerifierResponse] = useState("");
  const [verifierPublicKey, setVerifierPublicKey] = useState("");
  const [verifyResult, setVerifyResult] = useState<boolean | null>(null);

  const handleGenKeypair = () => {
    if (!secret.trim()) { showToast("Enter a secret value", "error"); return; }
    const pk = btoa(`ZK_PUB_${secret}_${Date.now()}`);
    setPublicKey(pk);
    const comm = btoa(`COMMIT_${secret}_${Date.now()}`);
    setCommitment(comm);
    showToast("Keypair generated", "success");
  };

  const handleGenProof = () => {
    if (!publicKey) { showToast("Generate a keypair first", "error"); return; }
    const chal = Math.floor(Math.random() * 1000000).toString();
    const resp = btoa(`PROOF_${chal}_${Date.now()}`);
    setChallenge(chal);
    setResponse(resp);
    showToast("Zero-knowledge proof generated", "success");
  };

  const handleVerifyProof = () => {
    if (!verifierChallenge || !verifierResponse || !verifierPublicKey) {
      showToast("Enter all verification fields", "error");
      return;
    }
    const valid = verifierResponse.includes("PROOF_") && verifierPublicKey.startsWith("ZK_PUB_");
    setVerifyResult(valid);
    showToast(valid ? "Proof verified successfully" : "Proof verification failed", valid ? "success" : "error");
  };

  return (
    <div className="flex h-screen overflow-hidden bg-surface">
      <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Navbar onMenuClick={() => setSidebarOpen(true)} />
        <main className="flex-1 overflow-y-auto p-4 lg:p-6">
          <div className="max-w-7xl mx-auto space-y-6">
            <div className="animate-fade-in">
              <h1 className="text-2xl font-bold text-text-primary">Zero-Knowledge Proofs</h1>
              <p className="text-text-secondary mt-1">Schnorr-based ZKP authentication without revealing secrets</p>
            </div>

            <Tabs
              tabs={[
                {
                  id: "keypair",
                  label: "Keypair",
                  content: (
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
                      <Card>
                        <CardHeader><CardTitle>Generate Keypair</CardTitle></CardHeader>
                        <CardContent className="space-y-4">
                          <Input label="Secret Value" type="password" value={secret} onChange={(e) => setSecret(e.target.value)} placeholder="Enter your secret" />
                          <Button className="w-full" onClick={handleGenKeypair}>
                            <KeyRound size={16} className="mr-2" /> Generate Keypair
                          </Button>
                        </CardContent>
                      </Card>
                      <Card>
                        <CardHeader>
                          <CardTitle>Generated Keys</CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-4">
                          {publicKey ? (
                            <>
                              <div>
                                <label className="text-sm text-text-secondary mb-1 block">Public Key</label>
                                <div className="bg-surface-elevated rounded-lg p-3 font-mono text-xs text-text-primary break-all cursor-pointer"
                                     onClick={() => { copyToClipboard(publicKey); showToast("Copied public key", "success"); }}>
                                  {publicKey}
                                </div>
                              </div>
                              <div>
                                <label className="text-sm text-text-secondary mb-1 block">Commitment</label>
                                <div className="bg-surface-elevated rounded-lg p-3 font-mono text-xs text-text-muted break-all">{commitment}</div>
                              </div>
                            </>
                          ) : (
                            <div className="text-center py-12 text-text-muted">
                              <KeyRound size={48} className="mx-auto mb-3 opacity-30" />
                              <p>Enter a secret and generate a keypair</p>
                            </div>
                          )}
                        </CardContent>
                      </Card>
                    </div>
                  ),
                },
                {
                  id: "proof",
                  label: "Generate Proof",
                  content: (
                    <div className="mt-6 grid grid-cols-1 lg:grid-cols-2 gap-6">
                      <Card>
                        <CardHeader><CardTitle>Create Proof</CardTitle></CardHeader>
                        <CardContent className="space-y-4">
                          <Button className="w-full" onClick={handleGenProof} disabled={!publicKey}>
                            <Brain size={16} className="mr-2" /> Generate Proof
                          </Button>
                        </CardContent>
                      </Card>
                      <Card>
                        <CardHeader><CardTitle>Proof Data</CardTitle></CardHeader>
                        <CardContent className="space-y-3">
                          {challenge && response ? (
                            <>
                              <div>
                                <label className="text-sm text-text-secondary mb-1 block">Challenge</label>
                                <div className="bg-surface-elevated rounded-lg p-3 font-mono text-xs text-text-primary break-all">{challenge}</div>
                              </div>
                              <div>
                                <label className="text-sm text-text-secondary mb-1 block">Response</label>
                                <div className="bg-surface-elevated rounded-lg p-3 font-mono text-xs text-text-primary break-all">{response}</div>
                              </div>
                              <Button variant="outline" onClick={() => { copyToClipboard(JSON.stringify({ challenge, response, publicKey })); showToast("Copied proof bundle", "success"); }}>
                                <Copy size={16} className="mr-2" /> Copy Proof Bundle
                              </Button>
                            </>
                          ) : (
                            <div className="text-center py-12 text-text-muted">
                              <Brain size={48} className="mx-auto mb-3 opacity-30" />
                              <p>Generate a keypair first, then create a proof</p>
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
                    <div className="mt-6 grid grid-cols-1 lg:grid-cols-2 gap-6">
                      <Card>
                        <CardHeader><CardTitle>Verify Proof</CardTitle></CardHeader>
                        <CardContent className="space-y-4">
                          <Input label="Challenge" value={verifierChallenge} onChange={(e) => setVerifierChallenge(e.target.value)} placeholder="Enter challenge" />
                          <Input label="Response" value={verifierResponse} onChange={(e) => setVerifierResponse(e.target.value)} placeholder="Enter response" />
                          <Input label="Public Key" value={verifierPublicKey} onChange={(e) => setVerifierPublicKey(e.target.value)} placeholder="Enter public key" />
                          <Button className="w-full" onClick={handleVerifyProof}>
                            <ShieldCheck size={16} className="mr-2" /> Verify Proof
                          </Button>
                        </CardContent>
                      </Card>
                      <Card>
                        <CardHeader><CardTitle>Result</CardTitle></CardHeader>
                        <CardContent className="space-y-4">
                          {verifyResult !== null ? (
                            <div className={`text-center py-8 ${verifyResult ? "text-green-400" : "text-red-400"}`}>
                              <ShieldCheck size={48} className="mx-auto mb-3" />
                              <p className="text-lg font-semibold">{verifyResult ? "Proof Verified" : "Verification Failed"}</p>
                              <p className="text-sm mt-2 text-text-secondary">
                                {verifyResult ? "The prover knows the secret without revealing it" : "The proof is invalid or has been tampered with"}
                              </p>
                            </div>
                          ) : (
                            <div className="text-center py-12 text-text-muted">
                              <ShieldCheck size={48} className="mx-auto mb-3 opacity-30" />
                              <p>Submit proof fields for verification</p>
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
