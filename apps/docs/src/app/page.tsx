import Link from 'next/link';

export default function HomePage() {
  return (
    <div>
      <div className="text-center py-16">
        <div className="w-16 h-16 rounded-2xl bg-[var(--vp-primary)] flex items-center justify-center text-white font-bold text-2xl mx-auto mb-6">
          V
        </div>
        <h1 className="text-5xl font-bold mb-4">
          VeilPass
        </h1>
        <p className="text-xl text-[var(--vp-text-secondary)] max-w-2xl mx-auto mb-8">
          Passwordless authentication and secure access management.
          Generate QR codes, NFC payloads, time-limited tokens, and signed links.
        </p>
        <div className="flex gap-4 justify-center">
          <Link
            href="/quickstart"
            className="inline-flex items-center px-6 py-3 rounded-lg bg-[var(--vp-primary)] text-white font-medium hover:bg-[var(--vp-primary-dark)] transition-colors no-underline"
          >
            Get Started
          </Link>
          <Link
            href="/installation"
            className="inline-flex items-center px-6 py-3 rounded-lg border border-[var(--vp-border)] text-[var(--vp-text)] font-medium hover:bg-[var(--vp-bg-secondary)] transition-colors no-underline"
          >
            Installation
          </Link>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-16">
        <div className="p-6 rounded-xl border border-[var(--vp-border)] bg-[var(--vp-bg-secondary)]">
          <div className="text-2xl mb-3">🔐</div>
          <h3 className="font-semibold text-lg mb-2">Passwordless Auth</h3>
          <p className="text-sm text-[var(--vp-text-secondary)]">
            Authenticate without passwords using QR codes, NFC, and cryptographic tokens.
          </p>
        </div>
        <div className="p-6 rounded-xl border border-[var(--vp-border)] bg-[var(--vp-bg-secondary)]">
          <div className="text-2xl mb-3">⚡</div>
          <h3 className="font-semibold text-lg mb-2">Multiple Formats</h3>
          <p className="text-sm text-[var(--vp-text-secondary)]">
            Generate QR codes, NFC payloads, JWTs, and signed URLs from a single CLI.
          </p>
        </div>
        <div className="p-6 rounded-xl border border-[var(--vp-border)] bg-[var(--vp-bg-secondary)]">
          <div className="text-2xl mb-3">🛡️</div>
          <h3 className="font-semibold text-lg mb-2">Security First</h3>
          <p className="text-sm text-[var(--vp-text-secondary)]">
            Time-limited tokens, one-time use links, and cryptographic signing built-in.
          </p>
        </div>
      </div>

      <div className="mb-16">
        <h2 className="text-2xl font-bold mb-6">Quick Links</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[
            { title: 'CLI Reference', href: '/cli', desc: 'Complete CLI command reference' },
            { title: 'REST API', href: '/api', desc: 'API endpoints and usage' },
            { title: 'SDK', href: '/sdk', desc: 'Language SDK documentation' },
            { title: 'Security', href: '/security', desc: 'Security model and best practices' },
            { title: 'Architecture', href: '/architecture', desc: 'System architecture overview' },
            { title: 'FAQ', href: '/faq', desc: 'Frequently asked questions' },
          ].map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className="p-4 rounded-lg border border-[var(--vp-border)] hover:border-[var(--vp-primary)] transition-colors no-underline group"
            >
              <h3 className="font-semibold group-hover:text-[var(--vp-primary)] transition-colors">{link.title}</h3>
              <p className="text-sm text-[var(--vp-text-secondary)] mt-1">{link.desc}</p>
            </Link>
          ))}
        </div>
      </div>

      <div className="text-center py-8 border-t border-[var(--vp-border)]">
        <p className="text-sm text-[var(--vp-text-secondary)]">
          VeilPass v0.1.0 &mdash; Open source under the MIT License
        </p>
      </div>
    </div>
  );
}
