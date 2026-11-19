// @vitest-environment node
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { NextRequest } from "next/server";
import nextConfig from "../../next.config";
import { GAME_NOT_FOUND_PATH, isUnpublishedGamePath, publishedGameIds } from "@/lib/gameRoute";

// Release 2.1.1, item 1 (docs/plans/2.1.1.md; Codex audit of PR #6, finding 5). In Next 16.4.6 a notFound() thrown while
// the game page renders sends an empty shell and leaves the not-found tree to the client, so with JavaScript off the body
// was empty. The proxy now rewrites an unknown or malformed /game/<id> to a server-rendered route with status 404.

const INDEX = JSON.parse(readFileSync(join(process.cwd(), "public/data/archive/index-2026.json"), "utf8"));
const PUBLISHED: number[] = INDEX.games.map((row: { game_pk: number }) => row.game_pk);

describe("publishedGameIds", () => {
  it("lists every game of the published index, as strings", () => {
    const ids = publishedGameIds(INDEX)!;
    expect(ids.size).toBe(PUBLISHED.length);
    for (const pk of PUBLISHED) expect(ids.has(String(pk))).toBe(true);
  });

  it("is null for an index that does not validate, so nothing is rewritten on a guess", () => {
    expect(publishedGameIds({ ...INDEX, archive_version: "2.0.0" })).toBeNull();
    expect(publishedGameIds(null)).toBeNull();
    expect(publishedGameIds({ games: "x" })).toBeNull();
  });
});

describe("isUnpublishedGamePath", () => {
  const ids = new Set(PUBLISHED.map(String));

  it("is true for an unknown, a malformed or an internal id under /game/", () => {
    for (const path of ["/game/123", "/game/abc", "/game/999999", "/game/0849799", "/game/%20", GAME_NOT_FOUND_PATH]) {
      expect(isUnpublishedGamePath(path, ids), path).toBe(true);
    }
  });

  it("is false for a published game and for paths that are not one game id (controls)", () => {
    for (const path of [`/game/${PUBLISHED[0]}`, `/game/${PUBLISHED.at(-1)}`, "/game", "/game/", "/archive", "/game/123/x", "/"]) {
      expect(isUnpublishedGamePath(path, ids), path).toBe(false);
    }
  });

  // Codex verification of PR #8, finding 2: 2.1.0 opened /game/%3849799 as game 849799, so the id is decoded once before
  // the lookup; an invalid escape cannot be decoded and is malformed.
  it("decodes the id once: a percent-encoded published id is a game, an encoded unknown id is not", () => {
    const encoded = `/game/%${PUBLISHED[0].toString().charCodeAt(0).toString(16)}${PUBLISHED[0].toString().slice(1)}`;
    expect(encoded).toBe("/game/%3849799");
    expect(isUnpublishedGamePath(encoded, ids)).toBe(false);
    expect(isUnpublishedGamePath("/game/%31%32%33", ids)).toBe(true);
    expect(isUnpublishedGamePath("/game/%253849799", ids)).toBe(true);
    expect(isUnpublishedGamePath("/game/%2F", ids)).toBe(true);
    expect(isUnpublishedGamePath("/game/%75nknown", ids)).toBe(true);
  });

  it("is true for an id with an invalid escape (malformed)", () => {
    for (const path of ["/game/%E0%A4%A", "/game/%", "/game/84979%9"]) expect(isUnpublishedGamePath(path, ids), path).toBe(true);
  });

  it("is false for every path when the ids are unknown (an index that did not validate)", () => {
    expect(isUnpublishedGamePath("/game/123", null)).toBe(false);
  });
});

describe("proxy on /game/<id>", () => {
  const rewriteOf = (response: Response) => response.headers.get("x-middleware-rewrite");

  for (const id of ["123", "abc"]) {
    it(`rewrites /game/${id} with status 404 to the server-rendered not-found route, with the same CSP and nonce`, async () => {
      const { proxy } = await import("../../proxy");
      const response = proxy(new NextRequest(`http://localhost/game/${id}`, { headers: { "x-nonce": "attacker" } }));
      expect(response.status).toBe(404);
      expect(new URL(rewriteOf(response)!).pathname).toBe(GAME_NOT_FOUND_PATH);
      const policy = response.headers.get("content-security-policy")!;
      const nonce = policy.match(/'nonce-([^']+)'/)![1];
      expect(nonce).toMatch(/^[A-Za-z0-9+/]{32}$/);
      expect(response.headers.get("x-middleware-request-x-nonce")).toBe(nonce);
      expect(response.headers.get("x-middleware-request-content-security-policy")).toBe(policy);
      expect(response.headers.get("cache-control")).toContain("no-store");
    });
  }

  // Release 2.1.1, Codex verification of PR #8, finding 1. Next's URL normalization turns 127.0.0.1 and [::1] into
  // localhost, so on a server bound to 127.0.0.1 the rewrite left the server's origin and was proxied as external, which
  // hung. `skipProxyUrlNormalize` keeps the request URL as sent; the build defines this env flag from it (define-env.js).
  // This pins the proxy's own output and the config key; that the adapter then passes the destination on as written is
  // proved in a real server by `scripts/check_release_b_browser.mjs notfound` on next start -H 127.0.0.1.
  describe("on a loopback host, with the env the build derives from next.config.ts", () => {
    let saved: string | undefined;
    beforeEach(() => {
      saved = process.env.__NEXT_NO_MIDDLEWARE_URL_NORMALIZE;
      if (nextConfig.skipProxyUrlNormalize) process.env.__NEXT_NO_MIDDLEWARE_URL_NORMALIZE = "true";
      else delete process.env.__NEXT_NO_MIDDLEWARE_URL_NORMALIZE;
    });
    afterEach(() => {
      if (saved === undefined) delete process.env.__NEXT_NO_MIDDLEWARE_URL_NORMALIZE;
      else process.env.__NEXT_NO_MIDDLEWARE_URL_NORMALIZE = saved;
    });

    // localhost is the control: normalization maps it to itself, so it kept the origin before the fix too.
    for (const origin of ["http://127.0.0.1:3082", "http://[::1]:3082", "http://localhost:3082"]) {
      it(`keeps the rewrite of /game/123 on the request's origin ${origin}`, async () => {
        const { proxy } = await import("../../proxy");
        const response = proxy(new NextRequest(`${origin}/game/123`));
        expect(response.status).toBe(404);
        const destination = new URL(rewriteOf(response)!);
        expect(destination.origin).toBe(origin);
        expect(destination.pathname).toBe(GAME_NOT_FOUND_PATH);
      });
    }
  });

  it("lets a percent-encoded published id through and rewrites an invalid escape (finding 2)", async () => {
    const { proxy } = await import("../../proxy");
    const encoded = proxy(new NextRequest("http://localhost/game/%3849799"));
    expect(encoded.status).toBe(200);
    expect(rewriteOf(encoded)).toBeNull();
    const malformed = proxy(new NextRequest("http://localhost/game/%E0%A4%A"));
    expect(malformed.status).toBe(404);
    expect(new URL(rewriteOf(malformed)!).pathname).toBe(GAME_NOT_FOUND_PATH);
  });

  it("lets a published game through untouched (control)", async () => {
    const { proxy } = await import("../../proxy");
    const response = proxy(new NextRequest(`http://localhost/game/${PUBLISHED[0]}`));
    expect(response.status).toBe(200);
    expect(rewriteOf(response)).toBeNull();
    expect(response.headers.get("content-security-policy")).toContain("'nonce-");
  });
});
