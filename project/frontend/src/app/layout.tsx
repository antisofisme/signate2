import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import '@/styles/globals.css';
import { cn } from '@/lib/utils';
import { Providers } from './providers';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: {
    default: 'Anthias - Multi-tenant SaaS Platform',
    template: '%s | Anthias',
  },
  description: 'A powerful multi-tenant SaaS platform with content management, user management, and analytics.',
  keywords: ['SaaS', 'multi-tenant', 'content management', 'dashboard', 'analytics'],
  authors: [{ name: 'Anthias Team' }],
  creator: 'Anthias',
  metadataBase: new URL(process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3000'),
  openGraph: {
    type: 'website',
    locale: 'en_US',
    url: process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3000',
    siteName: 'Anthias',
    title: 'Anthias - Multi-tenant SaaS Platform',
    description: 'A powerful multi-tenant SaaS platform with content management, user management, and analytics.',
    images: [
      {
        url: '/og-image.png',
        width: 1200,
        height: 630,
        alt: 'Anthias',
      },
    ],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Anthias - Multi-tenant SaaS Platform',
    description: 'A powerful multi-tenant SaaS platform with content management, user management, and analytics.',
    images: ['/og-image.png'],
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      'max-video-preview': -1,
      'max-image-preview': 'large',
      'max-snippet': -1,
    },
  },
  manifest: '/manifest.json',
  icons: {
    icon: '/favicon.ico',
    shortcut: '/favicon-16x16.png',
    apple: '/apple-touch-icon.png',
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={cn(inter.className, 'min-h-screen bg-background antialiased')}>
        <Providers>
          {children}
        </Providers>
      </body>
    </html>
  );
}