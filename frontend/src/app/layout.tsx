import type { Metadata, Viewport } from 'next';
import './globals.css';
import PWAInstall from '@/components/PWAInstall';

export const metadata: Metadata = {
  title: 'AI Outreach — Email Lead Generation Platform',
  description: 'AI-powered cold email outreach and lead generation SaaS',
  manifest: '/manifest.json',
  appleWebApp: {
    capable: true,
    statusBarStyle: 'default',
    title: 'AI Outreach',
  },
};

export const viewport: Viewport = {
  themeColor: '#2563eb',
  width: 'device-width',
  initialScale: 1,
  maximumScale: 1,
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <link rel="icon" href="/icons/icon-192.png" />
        <link rel="apple-touch-icon" href="/icons/icon-192.png" />
      </head>
      <body>
        {children}
        <PWAInstall />
      </body>
    </html>
  );
}
