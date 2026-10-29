import { Analytics } from "@vercel/analytics/next";
import type { Metadata as NextMetadata } from "next";
import localFont from "next/font/local";
import { headers } from "next/headers";
import "./globals.css";

const plexSans = localFont({
  src: [
    { path: "./fonts/ibm-plex-sans-latin-400-normal.woff2", weight: "400", style: "normal" },
    { path: "./fonts/ibm-plex-sans-latin-500-normal.woff2", weight: "500", style: "normal" },
    { path: "./fonts/ibm-plex-sans-latin-600-normal.woff2", weight: "600", style: "normal" },
    { path: "./fonts/ibm-plex-sans-latin-700-normal.woff2", weight: "700", style: "normal" },
  ],
  display: "swap",
  variable: "--font-sans",
});

const plexMono = localFont({
  src: [
    { path: "./fonts/ibm-plex-mono-latin-500-normal.woff2", weight: "500", style: "normal" },
    { path: "./fonts/ibm-plex-mono-latin-600-normal.woff2", weight: "600", style: "normal" },
  ],
  display: "swap",
  variable: "--font-mono",
});

export const metadata: NextMetadata = {
  title: "PitchCraft Matchup Agent",
  description: "Starting-pitcher matchup reports for MLB fans, checked against public data. No predictions, no betting.",
};

export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  // Nonces belong to individual requests; static/CDN HTML cannot reuse them.
  await headers();
  return (
    <html lang="en" className={`${plexSans.variable} ${plexMono.variable}`}>
      <body className="min-h-screen bg-neutral-100 font-sans text-neutral-900 antialiased">
        {children}
        {/* Vercel Web Analytics (D26): page views only, no custom event. */}
        <Analytics />
      </body>
    </html>
  );
}
