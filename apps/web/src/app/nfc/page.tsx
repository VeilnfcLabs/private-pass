"use client";

import React, { useState } from "react";
import { Sidebar } from "@/components/layout/sidebar";
import { Navbar } from "@/components/layout/navbar";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Select } from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs } from "@/components/ui/tabs";
import { useNFCStore } from "@/lib/stores/nfcStore";
import { showToast } from "@/components/ui/toast";
import { copyToClipboard, downloadFile } from "@/lib/utils";
import { Nfc, Copy, Download, Code } from "lucide-react";

export default function NFCPage() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const store = useNFCStore();

  const handleGenerate = () => {
    if (!store.payload.trim()) {
      showToast("Please enter a payload", "error");
      return;
    }
    showToast("NFC payload generated successfully", "success");
  };

  const outputTabs = [
    {
      id: "payload",
      label: "Payload",
      content: (
        <div className="space-y-4">
          <div className="bg-surface-elevated rounded-lg p-4 font-mono text-sm text-text-primary overflow-x-auto">
            {store.generatedPayload
              ? JSON.stringify(store.generatedPayload, null, 2)
              : "Generate a payload to see the output"}
          </div>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" leftIcon={<Copy size={14} />}>
              Copy
            </Button>
            <Button variant="outline" size="sm" leftIcon={<Download size={14} />}>
              JSON
            </Button>
          </div>
        </div>
      ),
    },
    {
      id: "hex",
      label: "HEX",
      content: (
        <div className="space-y-4">
          <div className="bg-surface-elevated rounded-lg p-4 font-mono text-sm text-text-primary overflow-x-auto">
            {store.hex || "No HEX data generated"}
          </div>
          <Button variant="outline" size="sm" leftIcon={<Copy size={14} />}>
            Copy HEX
          </Button>
        </div>
      ),
    },
    {
      id: "base64",
      label: "Base64",
      content: (
        <div className="space-y-4">
          <div className="bg-surface-elevated rounded-lg p-4 font-mono text-sm text-text-primary overflow-x-auto break-all">
            {store.base64 || "No Base64 data generated"}
          </div>
          <Button variant="outline" size="sm" leftIcon={<Copy size={14} />}>
            Copy Base64
          </Button>
        </div>
      ),
    },
    {
      id: "ndef",
      label: "NDEF",
      content: (
        <div className="space-y-4">
          <div className="bg-surface-elevated rounded-lg p-4 font-mono text-sm text-text-primary overflow-x-auto break-all">
            {store.ndef || "No NDEF data generated"}
          </div>
          <Button variant="outline" size="sm" leftIcon={<Copy size={14} />}>
            Copy NDEF
          </Button>
        </div>
      ),
    },
  ];

  return (
    <div className="flex h-screen overflow-hidden bg-surface">
      <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Navbar onMenuClick={() => setSidebarOpen(true)} />
        <main className="flex-1 overflow-y-auto p-4 lg:p-6">
          <div className="max-w-7xl mx-auto space-y-6">
            <div className="animate-fade-in">
              <h1 className="text-2xl font-bold text-text-primary">NFC Generator</h1>
              <p className="text-text-secondary mt-1">Create NFC payloads for physical authentication</p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Input Form */}
              <Card>
                <CardHeader>
                  <CardTitle>Configuration</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <Input
                    label="Issuer"
                    placeholder="VeilPass"
                    value={store.issuer}
                    onChange={(e) => store.setIssuer(e.target.value)}
                  />
                  <Textarea
                    label="Payload"
                    placeholder="Enter NFC payload content..."
                    value={store.payload}
                    onChange={(e) => store.setPayload(e.target.value)}
                    rows={4}
                  />
                  <div className="grid grid-cols-2 gap-4">
                    <Input
                      label="Version"
                      value={store.version}
                      onChange={(e) => store.setVersion(e.target.value)}
                      placeholder="1.0"
                    />
                    <Select
                      label="Type"
                      value={store.type}
                      onChange={(e) => store.setType(e.target.value as any)}
                      options={[
                        { value: "uri", label: "URI" },
                        { value: "text", label: "Text" },
                        { value: "smart_poster", label: "Smart Poster" },
                        { value: "mime", label: "MIME" },
                        { value: "external", label: "External" },
                      ]}
                    />
                  </div>
                  <Input
                    type="date"
                    label="Expiration"
                    value={store.expiration}
                    onChange={(e) => store.setExpiration(e.target.value)}
                  />
                  <Textarea
                    label="Metadata (JSON)"
                    placeholder='{"key": "value"}'
                    value={store.metadata}
                    onChange={(e) => store.setMetadata(e.target.value)}
                    rows={3}
                  />
                  <Button className="w-full" size="lg" onClick={handleGenerate}>
                    Generate NFC Payload
                  </Button>
                </CardContent>
              </Card>

              {/* Output */}
              <Card>
                <CardHeader>
                  <CardTitle>Output</CardTitle>
                </CardHeader>
                <CardContent>
                  <Tabs tabs={outputTabs} />
                </CardContent>
              </Card>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
