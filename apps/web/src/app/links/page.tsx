"use client";

import React, { useState } from "react";
import { Sidebar } from "@/components/layout/sidebar";
import { Navbar } from "@/components/layout/navbar";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { cn } from "@/lib/utils";
import { showToast } from "@/components/ui/toast";
import { Link as LinkIcon, Copy, RefreshCw } from "lucide-react";

const expirationPresets = [
  { value: "1h", label: "1 Hour" },
  { value: "6h", label: "6 Hours" },
  { value: "24h", label: "24 Hours" },
  { value: "7d", label: "7 Days" },
  { value: "30d", label: "30 Days" },
];

export default function LinksPage() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [resourceId, setResourceId] = useState("");
  const [expiration, setExpiration] = useState("24h");
  const [oneTimeUse, setOneTimeUse] = useState(false);
  const [maxUses, setMaxUses] = useState(1);
  const [generatedLink, setGeneratedLink] = useState<string | null>(null);

  const handleGenerate = () => {
    if (!resourceId.trim()) {
      showToast("Please enter a resource identifier", "error");
      return;
    }
    const link = `https://veilpass.dev/s/${resourceId}?exp=${expiration}&uses=${maxUses}`;
    setGeneratedLink(link);
    showToast("Signed link generated", "success");
  };

  return (
    <div className="flex h-screen overflow-hidden bg-surface">
      <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Navbar onMenuClick={() => setSidebarOpen(true)} />
        <main className="flex-1 overflow-y-auto p-4 lg:p-6">
          <div className="max-w-7xl mx-auto space-y-6">
            <div className="animate-fade-in">
              <h1 className="text-2xl font-bold text-text-primary">Signed Links</h1>
              <p className="text-text-secondary mt-1">Create time-limited signed links</p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Input Form */}
              <Card>
                <CardHeader>
                  <CardTitle>Configuration</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <Input
                    label="Resource Identifier"
                    placeholder="doc-123 or /api/resource/123"
                    value={resourceId}
                    onChange={(e) => setResourceId(e.target.value)}
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
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-text-secondary">One-time use</span>
                    <Switch checked={oneTimeUse} onChange={setOneTimeUse} />
                  </div>
                  <Input
                    type="number"
                    label="Max Uses"
                    value={maxUses}
                    onChange={(e) => setMaxUses(Number(e.target.value))}
                    min={1}
                  />
                  <Button className="w-full" size="lg" onClick={handleGenerate}>
                    Generate Signed Link
                  </Button>
                </CardContent>
              </Card>

              {/* Output */}
              <Card>
                <CardHeader>
                  <CardTitle>Generated Link</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  {generatedLink ? (
                    <>
                      <div className="bg-surface-elevated rounded-lg p-4">
                        <a
                          href={generatedLink}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-primary-400 hover:text-primary-300 break-all font-mono text-sm"
                        >
                          {generatedLink}
                        </a>
                      </div>
                      <div className="flex gap-2">
                        <Button variant="outline" leftIcon={<Copy size={16} />}>
                          Copy Link
                        </Button>
                        <Button variant="ghost" leftIcon={<RefreshCw size={16} />}>
                          Regenerate
                        </Button>
                      </div>
                    </>
                  ) : (
                    <div className="text-center py-12 text-text-muted">
                      <LinkIcon size={48} className="mx-auto mb-3 opacity-30" />
                      <p>Generate a signed link to see the result</p>
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
