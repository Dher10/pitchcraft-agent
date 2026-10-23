import { Analytics } from "@vercel/analytics/next";
import type { Metadata as NextMetadata } from "next";
import { IBM_Plex_Mono, IBM_Plex_Sans } from "next/font/google";
import "./globals.css";

const plexSans = IBM_Plex_Sans({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  display: "swap",
  variable: "--font-sans",
});

const plexMono = IBM_Plex_Mono({
  subsets: ["latin"],
  weight: ["500", "600"],
  display: "swap",
  variable: "--font-mono",
});

export const metadata: NextMetadata = {
  title: "PitchCraft Matchup Agent",
  description: "Starting-pitcher matchup reports for MLB fans, checked against public data. No predictions, no betting.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
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
