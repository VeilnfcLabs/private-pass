'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

interface NavItem {
  title: string;
  href: string;
}

interface NavSection {
  title: string;
  items: NavItem[];
}

const navSections: NavSection[] = [
  {
    title: 'Getting Started',
    items: [
      { title: 'Introduction', href: '/introduction' },
      { title: 'Installation', href: '/installation' },
      { title: 'Quick Start', href: '/quickstart' },
    ],
  },
  {
    title: 'Reference',
    items: [
      { title: 'CLI Reference', href: '/cli' },
      { title: 'REST API', href: '/api' },
      { title: 'SDK', href: '/sdk' },
    ],
  },
  {
    title: 'Topics',
    items: [
      { title: 'Security', href: '/security' },
      { title: 'Architecture', href: '/architecture' },
    ],
  },
  {
    title: 'Community',
    items: [
      { title: 'FAQ', href: '/faq' },
      { title: 'Contributing', href: '/contributing' },
    ],
  },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 min-h-screen border-r border-[var(--vp-border)] bg-[var(--vp-bg-secondary)] overflow-y-auto fixed left-0 top-0">
      <div className="p-4 border-b border-[var(--vp-border)]">
        <Link href="/" className="flex items-center gap-2 no-underline">
          <div className="w-8 h-8 rounded-lg bg-[var(--vp-primary)] flex items-center justify-center text-white font-bold text-sm">
            V
          </div>
          <span className="font-bold text-lg text-[var(--vp-text)]">VeilPass</span>
        </Link>
      </div>

      <nav className="py-2">
        {navSections.map((section) => (
          <div key={section.title}>
            <div className="sidebar-section">{section.title}</div>
            {section.items.map((item) => {
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`sidebar-link ${isActive ? 'active' : ''}`}
                >
                  {item.title}
                </Link>
              );
            })}
          </div>
        ))}
      </nav>

      <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-[var(--vp-border)]">
        <a
          href="https://github.com/veilpass/veilpass"
          target="_blank"
          rel="noopener noreferrer"
          className="sidebar-link text-xs flex items-center gap-2"
        >
          <span>GitHub</span>
          <span className="text-[var(--vp-text-secondary)]">v0.1.0</span>
        </a>
      </div>
    </aside>
  );
}
