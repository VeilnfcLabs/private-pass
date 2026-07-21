"use client";

import React, { useState } from "react";
import { Sidebar } from "@/components/layout/sidebar";
import { Navbar } from "@/components/layout/navbar";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { cn } from "@/lib/utils";
import { showToast } from "@/components/ui/toast";
import { Globe, Copy, RefreshCw } from "lucide-react";

const expirationPresets = [
  { value: "1h", label: "1 Hour" },
  { value: "6h", label: "6 Hours" },
  { value: "24h", label: "24 Hours" },
  { value: "7d", label: "7 Days" },
  { value: "30d", label: "30 Days" },
];

export default function SignedUrlsPage() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [fileUrl, setFileUrl] = useState("");
  const [permissions, setPermissions] = useState("read");
  const [expiration, setExpiration] = useState("24h");
  const [downloadLimit, setDownloadLimit] = useState(0);
  const [oneTimeAccess, setOneTimeAccess] = useState(false);
  const [signedUrl, setSignedUrl] = useState<string | null>(null);

  const handleGenerate = () => {
    if (!fileUrl.trim()) {
      showToast("Please enter a URL", "error");
      return;
    }
    const url = `https://veilpass.dev/download?url=${encodeURIComponent(fileUrl)}&perm=${permissions}&exp=${expiration}`;
    setSignedUrl(url);
    showToast("Signed URL generated", "success");
  };

  return (
    <div className="flex h-screen overflow-hidden bg-surface">
      <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Navbar onMenuClick={() => setSidebarOpen(true)} />
        <main className="flex-1 overflow-y-auto p-4 lg:p-6">
          <div className="max-w-7xl mx-auto space-y-6">
            <div className="animate-fade-in">
              <h1 className="text-2xl font-bold text-text-primary">Signed URLs</h1>
              <p className="text-text-secondary mt-1">Create time-limited signed URLs for secure access</p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Input Form */}
              <Card>
                <CardHeader>
                  <CardTitle>Configuration</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <Input
                    label="File URL or Raw URL"
                    placeholder="https://storage.example.com/file.pdf"
                    value={fileUrl}
                    onChange={(e) => setFileUrl(e.target.value)}
                  />
                  <Select
                    label="Permissions"
                    value={permissions}
                    onChange={(e) => setPermissions(e.target.value)}
                    options={[
                      { value: "read", label: "Read" },
                      { value: "write", label: "Write" },
                      { value: "read+write", label: "Read + Write" },
                    ]}
                  />
                  <div>
                    <label className="text-sm text-text-secondary mb-2 block">Expiration</label>
                    <div className="flex flex-wrap gap-2">
                      {expirationPresets.map((preset) => (
                        <button
                          key={preset.value}
                          onClick={() => setExpiration(preset.value)}
                          className={cn(
                            "px-3 py-1.5 rounded-lg text-xs font-medium border transition-all",
                            expiration === preset.value
                              ? "border-primary-500 bg-primary-500/10 text-primary-400"
                              : "border-border text-text-secondary hover:border-primary-500/50"
                          )}
                        >
                          {preset.label}
                        </button>
                      ))}
                    </div>
                  )}
                  <Input
                    type="number"
                    label="Download Count Limit"
                    value={downloadLimit}
                    onChange={(e) => setDownloadLimit(Number(e.target.value))}
                    min={0}
                    placeholder="0 = unlimited"
                  />
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-text-secondary">One-time access</span>
                    <Switch checked={oneTimeAccess} onChange={setOneTimeAccess} />
                  </div>
                  <Button className="w-full" size="lg" onClick={handleGenerate}>
                    Generate Signed URL
                  </Button>
                </CardContent>
              </Card>

              {/* Output */}
              <Card>
                <CardHeader>
                  <CardTitle>Generated URL</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  {signedUrl ? (
                    <>
                      <div className="bg-surface-elevated rounded-lg p-4">
                        <a
                          href={signedUrl}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-primary-400 hover:text-primary-300 break-all font-mono text-sm"
                        >
                          {signedUrl}
                        </a>
                      </div>
                      <div className="flex gap-2">
                        <Button variant="outline" leftIcon={<Copy size={16} />}>
                          Copy URL
                        </Button>
                        <Button variant="ghost" leftIcon={<RefreshCw size={16} />}>
                          Regenerate
                        </Button>
                      </div>
                    </>
                  ) : (
                    <div className="text-center py-12 text-text-muted">
                      <Globe size={48} className="mx-auto mb-3 opacity-30" />
                      <p>Generate a signed URL to see the result</p>
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
