"use client";

import React, { useState } from "react";
import { Sidebar } from "@/components/layout/sidebar";
import { Navbar } from "@/components/layout/navbar";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Select } from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Slider } from "@/components/ui/slider";
import { Switch } from "@/components/ui/switch";
import { useQRStore } from "@/lib/stores/qrStore";
import { showToast } from "@/components/ui/toast";
import { QrCode, Download, Copy } from "lucide-react";

export default function QRPage() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const store = useQRStore();

  const handleGenerate = () => {
    if (!store.url.trim()) {
      showToast("Please enter a URL or text", "error");
      return;
    }
    showToast("QR code generated successfully", "success");
  };

  return (
    <div className="flex h-screen overflow-hidden bg-surface">
      <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Navbar onMenuClick={() => setSidebarOpen(true)} />
        <main className="flex-1 overflow-y-auto p-4 lg:p-6">
          <div className="max-w-7xl mx-auto space-y-6">
            <div className="animate-fade-in">
              <h1 className="text-2xl font-bold text-text-primary">QR Generator</h1>
              <p className="text-text-secondary mt-1">Create secure QR codes with advanced options</p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Input Form */}
              <Card>
                <CardHeader>
                  <CardTitle>Configuration</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <Textarea
                    label="Destination URL / Text"
                    placeholder="https://example.com or any text..."
                    value={store.url}
                    onChange={(e) => store.setUrl(e.target.value)}
                    rows={3}
                  />
                  <div className="grid grid-cols-2 gap-4">
                    <Select
                      label="Format"
                      value={store.format}
                      onChange={(e) => store.setFormat(e.target.value as "png" | "svg")}
                      options={[
                        { value: "png", label: "PNG" },
                        { value: "svg", label: "SVG" },
                      ]}
                    />
                    <Select
                      label="Error Correction"
                      value={store.errorCorrection}
                      onChange={(e) => store.setErrorCorrection(e.target.value as "L" | "M" | "Q" | "H")}
                      options={[
                        { value: "L", label: "Low (L)" },
                        { value: "M", label: "Medium (M)" },
                        { value: "Q", label: "Quartile (Q)" },
                        { value: "H", label: "High (H)" },
                      ]}
                    />
                  </div>
                  <Slider
                    label="Size"
                    value={store.size}
                    onChange={store.setSize}
                    min={128}
                    max={1024}
                    step={32}
                  />
                  <Slider
                    label="Margin"
                    value={store.margin}
                    onChange={store.setMargin}
                    min={0}
                    max={8}
                    step={1}
                  />
                  <div className="grid grid-cols-2 gap-4">
                    <div className="flex flex-col gap-1.5">
                      <label className="text-sm text-text-secondary">Color</label>
                      <input
                        type="color"
                        value={store.color}
                        onChange={(e) => store.setColor(e.target.value)}
                        className="w-full h-10 rounded-lg border border-border bg-surface-elevated cursor-pointer"
                      />
                    </div>
                    <div className="flex flex-col gap-1.5">
                      <label className="text-sm text-text-secondary">Background</label>
                      <input
                        type="color"
                        value={store.bgColor}
                        onChange={(e) => store.setBgColor(e.target.value)}
                        className="w-full h-10 rounded-lg border border-border bg-surface-elevated cursor-pointer"
                      />
                    </div>
                  </div>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-text-secondary">Expiration</span>
                      <Switch
                        checked={store.expirationEnabled}
                        onChange={store.setExpirationEnabled}
                      />
                    </div>
                    {store.expirationEnabled && (
                      <Input
                        type="number"
                        label="Duration (hours)"
                        value={store.expirationDuration}
                        onChange={(e) => store.setExpirationDuration(Number(e.target.value))}
                        min={1}
                      />
                    )}
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-text-secondary">One-time use</span>
                      <Switch
                        checked={store.oneTimeUse}
                        onChange={store.setOneTimeUse}
                      />
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-text-secondary">Include signature</span>
                      <Switch
                        checked={store.includeSignature}
                        onChange={store.setIncludeSignature}
                      />
                    </div>
                  </div>
                  <Button className="w-full" size="lg" onClick={handleGenerate}>
                    Generate QR Code
                  </Button>
                </CardContent>
              </Card>

              {/* Preview */}
              <Card>
                <CardHeader>
                  <CardTitle>Preview</CardTitle>
                </CardHeader>
                <CardContent className="flex flex-col items-center gap-4">
                  <div className="w-64 h-64 bg-white rounded-xl flex items-center justify-center border border-border">
                    {store.url ? (
                      <div className="text-center p-4">
                        <QrCode size={120} className="text-primary-500 mx-auto mb-2" />
                        <p className="text-xs text-text-muted">QR preview will render here</p>
                      </div>
                    ) : (
                      <div className="text-center text-text-muted">
                        <QrCode size={64} className="mx-auto mb-2 opacity-30" />
                        <p className="text-sm">Enter content to generate</p>
                      </div>
                    )}
                  </div>
                  {store.url && (
                    <div className="flex gap-2 w-full">
                      <Button variant="outline" leftIcon={<Download size={16} />} className="flex-1">
                        PNG
                      </Button>
                      <Button variant="outline" leftIcon={<Download size={16} />} className="flex-1">
                        SVG
                      </Button>
                      <Button variant="ghost" leftIcon={<Copy size={16} />}>
                        Copy
                      </Button>
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
