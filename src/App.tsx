import { useState } from "react";

function App() {
  const [activeTab, setActiveTab] = useState<string>("qr");

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100">
      {/* Header */}
      <header className="border-b border-gray-800 px-6 py-4">
        <h1 className="text-xl font-semibold tracking-tight">VeilPass</h1>
        <p className="text-sm text-gray-400 mt-1">
          Privacy QR &amp; NFC Generator
        </p>
      </header>

      {/* Navigation */}
      <nav className="border-b border-gray-800 px-6 flex gap-6 text-sm">
        {[
          { id: "qr", label: "QR Code" },
          { id: "nfc", label: "NFC Tag" },
          { id: "links", label: "Claim Link" },
          { id: "tokens", label: "Tokens" },
          { id: "keys", label: "Keys" },
          { id: "verify", label: "Verify" },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`py-3 border-b-2 transition-colors ${
              activeTab === tab.id
                ? "border-blue-500 text-blue-400"
                : "border-transparent text-gray-400 hover:text-gray-200"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </nav>

      {/* Content Area */}
      <main className="p-6">
        {activeTab === "qr" && <QrPanel />}
        {activeTab === "nfc" && <NfcPanel />}
        {activeTab === "links" && <LinksPanel />}
        {activeTab === "tokens" && <TokensPanel />}
        {activeTab === "keys" && <KeysPanel />}
        {activeTab === "verify" && <VerifyPanel />}
      </main>
    </div>
  );
}

/* ─── Panel Components ───────────────────────────────────────── */

function QrPanel() {
  const [content, setContent] = useState("");
  const [format, setFormat] = useState<"png" | "svg">("png");
  const [ecl, setEcl] = useState("H");

  return (
    <div className="max-w-2xl space-y-6">
      <h2 className="text-lg font-medium">Generate QR Code</h2>

      <div className="space-y-4">
        <div>
          <label className="block text-sm text-gray-400 mb-1">Content</label>
          <input
            type="text"
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="Enter URL or text..."
            className="w-full px-3 py-2 bg-gray-900 border border-gray-700 rounded-lg text-gray-100 placeholder-gray-500 focus:outline-none focus:border-blue-500"
          />
        </div>

        <div className="flex gap-4">
          <div className="flex-1">
            <label className="block text-sm text-gray-400 mb-1">Format</label>
            <select
              value={format}
              onChange={(e) => setFormat(e.target.value as "png" | "svg")}
              className="w-full px-3 py-2 bg-gray-900 border border-gray-700 rounded-lg text-gray-100 focus:outline-none focus:border-blue-500"
            >
              <option value="png">PNG</option>
              <option value="svg">SVG</option>
            </select>
          </div>
          <div className="flex-1">
            <label className="block text-sm text-gray-400 mb-1">
              Error Correction
            </label>
            <select
              value={ecl}
              onChange={(e) => setEcl(e.target.value)}
              className="w-full px-3 py-2 bg-gray-900 border border-gray-700 rounded-lg text-gray-100 focus:outline-none focus:border-blue-500"
            >
              <option value="L">Low (7%)</option>
              <option value="M">Medium (15%)</option>
              <option value="Q">Quartile (25%)</option>
              <option value="H">High (30%)</option>
            </select>
          </div>
        </div>

        <button
          disabled={!content}
          className="px-6 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 disabled:text-gray-500 rounded-lg font-medium transition-colors"
        >
          Generate QR Code
        </button>
      </div>

      {/* Preview placeholder */}
      <div className="border-2 border-dashed border-gray-700 rounded-xl p-12 flex items-center justify-center">
        <p className="text-gray-500 text-sm">
          {content
            ? "QR code preview will appear here"
            : "Enter content to generate a QR code"}
        </p>
      </div>
    </div>
  );
}

function NfcPanel() {
  return (
    <div className="max-w-2xl space-y-6">
      <h2 className="text-lg font-medium">Generate NFC NDEF Payload</h2>
      <p className="text-sm text-gray-400">
        Create NDEF messages for writing to NFC tags.
      </p>

      <div className="border-2 border-dashed border-gray-700 rounded-xl p-12 flex items-center justify-center">
        <p className="text-gray-500 text-sm">
          NFC tag generation form coming soon
        </p>
      </div>
    </div>
  );
}

function LinksPanel() {
  return (
    <div className="max-w-2xl space-y-6">
      <h2 className="text-lg font-medium">Secure Claim Links</h2>
      <p className="text-sm text-gray-400">
        Generate cryptographically signed claim links that can be embedded in QR
        codes or NFC tags.
      </p>

      <div className="border-2 border-dashed border-gray-700 rounded-xl p-12 flex items-center justify-center">
        <p className="text-gray-500 text-sm">
          Claim link form coming soon
        </p>
      </div>
    </div>
  );
}

function TokensPanel() {
  return (
    <div className="max-w-2xl space-y-6">
      <h2 className="text-lg font-medium">Time-Limited Tokens</h2>
      <p className="text-sm text-gray-400">
        Generate Ed25519-signed bearer tokens with configurable expiry.
      </p>

      <div className="border-2 border-dashed border-gray-700 rounded-xl p-12 flex items-center justify-center">
        <p className="text-gray-500 text-sm">
          Token generation form coming soon
        </p>
      </div>
    </div>
  );
}

function KeysPanel() {
  return (
    <div className="max-w-2xl space-y-6">
      <h2 className="text-lg font-medium">Key Management</h2>
      <p className="text-sm text-gray-400">
        Manage your Ed25519 signing keys. Keys are stored securely in your OS
        keychain.
      </p>

      <div className="border-2 border-dashed border-gray-700 rounded-xl p-12 flex items-center justify-center">
        <p className="text-gray-500 text-sm">
          Key management UI coming soon
        </p>
      </div>
    </div>
  );
}

function VerifyPanel() {
  return (
    <div className="max-w-2xl space-y-6">
      <h2 className="text-lg font-medium">Verify Tokens &amp; Links</h2>
      <p className="text-sm text-gray-400">
        Verify the authenticity of tokens, claim links, and signed URLs.
      </p>

      <div className="border-2 border-dashed border-gray-700 rounded-xl p-12 flex items-center justify-center">
        <p className="text-gray-500 text-sm">
          Verification form coming soon
        </p>
      </div>
    </div>
  );
}

export default App;
