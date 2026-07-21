import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { ThemeProvider } from "@/components/layout/theme-provider";
import { ToastContainer } from "@/components/ui/toast";

const inter = Inter({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-inter",
});

export const metadata: Metadata = {
  title: "VeilPass - Privacy QR & NFC Generator",
  description:
    "Generate secure links, QR codes, NFC payloads, signed URLs, and time-limited tokens.",
  keywords: [
    "QR code",
    "NFC",
    "signed URLs",
    "tokens",
    "privacy",
    "security",
    "VeilPass",
  ],
  authors: [{ name: "Veil Labs" }],
  openGraph: {
    title: "VeilPass - Privacy QR & NFC Generator",
    description:
      "Generate secure links, QR codes, NFC payloads, signed URLs, and time-limited tokens.",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark" suppressHydrationWarning>
      <body className={`${inter.variable} font-sans antialiased`}>
        <ThemeProvider>{children}</ThemeProvider>
        <ToastContainer />
      </body>
    </html>
  );
}
