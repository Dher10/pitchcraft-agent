import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // The proxy sees the request URL as sent (release 2.1.1). Next's normalization turned 127.0.0.1 and [::1] into localhost,
  // so on a server bound to 127.0.0.1 the /game not-found rewrite left the server's origin and hung as an external proxy.
  skipProxyUrlNormalize: true,
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
