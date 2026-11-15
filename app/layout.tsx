import { Analytics } from "@vercel/analytics/next";
import type { Metadata as NextMetadata } from "next";
import localFont from "next/font/local";
import { headers } from "next/headers";
import "./globals.css";
import SiteFooter from "@/components/site/SiteFooter";
import SiteHeader from "@/components/site/SiteHeader";
import { getPitchCraftData } from "@/lib/data";
import { seasonMode, type SeasonMode } from "@/lib/season";

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

// Display face of the design system (D67): page titles, names in heads, the wordmark and every featured number.
const bigShoulders = localFont({
  src: [{ path: "./fonts/big-shoulders-display-latin-wght-normal.woff2", weight: "100 900", style: "normal" }],
  display: "swap",
  variable: "--font-display",
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

/** The season switch reads the daily file; a file that cannot be read gives the off season, never a made-up game day. */
async function currentSeason(): Promise<SeasonMode> {
  try {
    return seasonMode(await getPitchCraftData());
  } catch {
    return "off_season";
  }
}

export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  // Nonces belong to individual requests; static/CDN HTML cannot reuse them.
  await headers();
  return (
    <html lang="en" className={`${plexSans.variable} ${plexMono.variable} ${bigShoulders.variable}`}>
      <body className="flex min-h-screen flex-col bg-ground font-sans text-ink antialiased">
        <SiteHeader season={await currentSeason()} />
        <div className="flex-1">{children}</div>
        <SiteFooter />
        {/* Vercel Web Analytics (D26): page views only, no custom event. */}
        <Analytics />
      </body>
    </html>
  );
}
