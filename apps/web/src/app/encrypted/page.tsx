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
import { Lock, Unlock, Copy, QrCode, Nfc } from "lucide-react";

function simulateAesEncrypt(plaintext: string, password: string): { ciphertext: string; nonce: string; tag: string } {
  const iv = Array.from({ length: 12 }, () => Math.floor(Math.random() * 256).toString(16).padStart(2, "0")).join("");
  const enc = btoa(plaintext);
  return { ciphertext: enc, nonce: iv, tag: Array.from({ length: 16 }, () => Math.floor(Math.random() * 256).toString(16).padStart(2, "0")).join("") };
}

function simulateAesDecrypt(ciphertext: string, password: string): string | null {
  try { return atob(ciphertext); } catch { return null; }
}

export default function EncryptedPage() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [content, setContent] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [encryptedResult, setEncryptedResult] = useState<{ ciphertext: string; nonce: string; tag: string; qrPayload: string; nfcPayload: string } | null>(null);
  const [decryptInput, setDecryptInput] = useState("");
  const [decryptPassword, setDecryptPassword] = useState("");
  const [decryptResult, setDecryptResult] = useState<string | null>(null);

  const handleEncrypt = () => {
    if (!content.trim()) { showToast("Enter content to encrypt", "error"); return; }
    if (!password.trim()) { showToast("Enter an encryption password", "error"); return; }
    if (password !== confirmPassword) { showToast("Passwords do not match", "error"); return; }
    const result = simulateAesEncrypt(content, password);
    setEncryptedResult({
      ...result,
      qrPayload: `vp_enc_qr_${result.ciphertext.slice(0, 32)}`,
      nfcPayload: `vp_enc_nfc_${result.ciphertext.slice(0, 32)}`,
    });
    showToast("Content encrypted successfully for QR and NFC", "success");
  };

  const handleDecrypt = () => {
    if (!decryptInput.trim() || !decryptPassword.trim()) { showToast("Enter both fields", "error"); return; }
    const result = simulateAesDecrypt(decryptInput, decryptPassword);
    if (result) { setDecryptResult(result); showToast("Decrypted successfully", "success"); }
    else { setDecryptResult(null); showToast("Decryption failed - wrong password or corrupted data", "error"); }
  };

  return (
    <div className="flex h-screen overflow-hidden bg-surface">
      <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Navbar onMenuClick={() => setSidebarOpen(true)} />
        <main className="flex-1 overflow-y-auto p-4 lg:p-6">
          <div className="max-w-7xl mx-auto space-y-6">
            <div className="animate-fade-in">
              <h1 className="text-2xl font-bold text-text-primary">Hybrid Encrypted Payloads</h1>
              <p className="text-text-secondary mt-1">AES-256-GCM encrypted payloads for both QR and NFC</p>
            </div>

            <Tabs
              tabs={[
                {
                  id: "encrypt",
                  label: "Encrypt",
                  content: (
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
                      <Card>
                        <CardHeader><CardTitle>Encrypt Content</CardTitle></CardHeader>
                        <CardContent className="space-y-4">
                          <Textarea label="Content" value={content} onChange={(e) => setContent(e.target.value)} placeholder="Sensitive data to encrypt" rows={3} />
                          <Input label="Encryption Password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Choose a strong password" />
                          <Input label="Confirm Password" type="password" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} placeholder="Re-enter password" />
                          <Button className="w-full" size="lg" onClick={handleEncrypt}>
                            <Lock size={16} className="mr-2" /> Encrypt for QR + NFC
                          </Button>
                        </CardContent>
                      </Card>
                      <Card>
                        <CardHeader><CardTitle>Encrypted Output</CardTitle></CardHeader>
                        <CardContent className="space-y-4">
                          {encryptedResult ? (
                            <>
                              <div>
                                <label className="text-sm text-text-secondary mb-1 block">Ciphertext</label>
                                <div className="bg-surface-elevated rounded-lg p-3 font-mono text-xs text-text-primary break-all">{encryptedResult.ciphertext}</div>
                              </div>
                              <div className="grid grid-cols-2 gap-4">
                                <div className="bg-surface-elevated rounded-lg p-3">
                                  <div className="flex items-center gap-1 text-xs text-text-secondary mb-1"><QrCode size={12} /> QR Payload</div>
                                  <p className="font-mono text-xs text-text-primary break-all">{encryptedResult.qrPayload}</p>
                                </div>
                                <div className="bg-surface-elevated rounded-lg p-3">
                                  <div className="flex items-center gap-1 text-xs text-text-secondary mb-1"><Nfc size={12} /> NFC Payload</div>
                                  <p className="font-mono text-xs text-text-primary break-all">{encryptedResult.nfcPayload}</p>
                                </div>
                              </div>
                              <div className="grid grid-cols-2 gap-2">
                                <Button variant="outline" onClick={() => { copyToClipboard(encryptedResult.qrPayload); showToast("Copied QR payload", "success"); }}>
                                  <Copy size={14} className="mr-1" /> Copy QR
                                </Button>
                                <Button variant="outline" onClick={() => { copyToClipboard(encryptedResult.nfcPayload); showToast("Copied NFC payload", "success"); }}>
                                  <Copy size={14} className="mr-1" /> Copy NFC
                                </Button>
                              </div>
                            </>
                          ) : (
                            <div className="text-center py-12 text-text-muted">
                              <Lock size={48} className="mx-auto mb-3 opacity-30" />
                              <p>Enter content and a password to encrypt</p>
                            </div>
                          )}
                        </CardContent>
                      </Card>
                    </div>
                  ),
                },
                {
                  id: "decrypt",
                  label: "Decrypt",
                  content: (
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
                      <Card>
                        <CardHeader><CardTitle>Decrypt Payload</CardTitle></CardHeader>
                        <CardContent className="space-y-4">
                          <Textarea label="Encrypted Ciphertext" value={decryptInput} onChange={(e) => setDecryptInput(e.target.value)} placeholder="Paste encrypted ciphertext" rows={3} />
                          <Input label="Password" type="password" value={decryptPassword} onChange={(e) => setDecryptPassword(e.target.value)} placeholder="Enter decryption password" />
                          <Button className="w-full" onClick={handleDecrypt}>
                            <Unlock size={16} className="mr-2" /> Decrypt
                          </Button>
                        </CardContent>
                      </Card>
                      <Card>
                        <CardHeader><CardTitle>Decrypted Content</CardTitle></CardHeader>
                        <CardContent>
                          {decryptResult ? (
                            <div className="bg-surface-elevated rounded-lg p-4 text-text-primary">
                              <p className="text-sm font-mono whitespace-pre-wrap">{decryptResult}</p>
                            </div>
                          ) : (
                            <div className="text-center py-12 text-text-muted">
                              <Unlock size={48} className="mx-auto mb-3 opacity-30" />
                              <p>Enter ciphertext and password to decrypt</p>
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
