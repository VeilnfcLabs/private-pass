import type { Metadata } from 'next';
import './globals.css';
import Sidebar from '../components/sidebar';

export const metadata: Metadata = {
  title: 'VeilPass Documentation',
  description: 'Documentation for VeilPass - Passwordless authentication and secure access management',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen">
        <Sidebar />
        <main className="ml-64 p-8 max-w-4xl">
          <div className="prose prose-invert max-w-none">
            {children}
          </div>
        </main>
      </body>
    </html>
  );
}
