import type { Metadata as NextMetadata } from "next";
import { Archivo, Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
  display: "swap",
});

const archivo = Archivo({
  variable: "--font-archivo",
  subsets: ["latin"],
  display: "swap",
});

export const metadata: NextMetadata = {
  title: "PitchCraft Matchup Agent",
  description: "Cached demo scouting report for an MLB starting-pitcher matchup.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${inter.variable} ${archivo.variable} h-full antialiased`}
    >
      <body className="min-h-full bg-[#F7F8FA] font-sans">{children}</body>
    </html>
  );
}
