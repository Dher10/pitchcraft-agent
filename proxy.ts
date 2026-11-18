import { NextRequest, NextResponse } from "next/server";
import { GAME_NOT_FOUND_PATH, isUnpublishedGamePath, publishedGameIds } from "./lib/gameRoute";
import archiveIndex from "./public/data/archive/index-2026.json";

// The published game ids, bundled at build so they follow each deploy. An unknown or malformed /game/<id> is rewritten,
// with status 404, to a server-rendered not-found route (release 2.1.1); null (an index that does not validate) rewrites nothing.
const GAME_IDS = publishedGameIds(archiveIndex);

// Both request and response carry the same policy: Next reads it to nonce its
// bootstrap scripts. Client-supplied headers never choose the trusted nonce.
export function proxy(request: NextRequest) {
  const nonce = Buffer.from(crypto.getRandomValues(new Uint8Array(24))).toString("base64");
  const policy = [
    "default-src 'self'",
    `script-src 'self' 'nonce-${nonce}'`,
    `style-src 'self' 'nonce-${nonce}'`,
    "style-src-attr 'unsafe-inline'",
    "connect-src 'self'",
    "font-src 'self'",
    "img-src 'self' data:",
    "object-src 'none'",
    "frame-src 'none'",
    "frame-ancestors 'none'",
    "base-uri 'self'",
    // Same-origin forms only: the archive filters are a plain GET form that must work without JavaScript (2026-11-17).
    "form-action 'self'",
  ].join("; ");
  const headers = new Headers(request.headers);
  headers.set("x-nonce", nonce);
  headers.set("Content-Security-Policy", policy);
  const response = isUnpublishedGamePath(request.nextUrl.pathname, GAME_IDS)
    ? NextResponse.rewrite(new URL(GAME_NOT_FOUND_PATH, request.url), { request: { headers }, status: 404 })
    : NextResponse.next({ request: { headers } });
  response.headers.set("Content-Security-Policy", policy);
  response.headers.set("Cache-Control", "private, no-store");
  return response;
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico|data/).*)"],
};
