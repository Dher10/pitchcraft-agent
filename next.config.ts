import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async headers() {
    return [
      {
        source: "/:path*",
        headers: [
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "X-Frame-Options", value: "DENY" },
        ],
      },
      ...["/data/:path*", "/_next/static/:path*", "/favicon.ico"].map((source) => ({
        source,
        headers: [{
          key: "Content-Security-Policy",
          value: "default-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'",
        }],
      })),
    ];
  },
};

export default nextConfig;
