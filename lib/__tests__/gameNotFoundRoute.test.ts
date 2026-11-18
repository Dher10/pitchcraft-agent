// @vitest-environment node
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";
import { NextRequest } from "next/server";
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

  it("lets a published game through untouched (control)", async () => {
    const { proxy } = await import("../../proxy");
    const response = proxy(new NextRequest(`http://localhost/game/${PUBLISHED[0]}`));
    expect(response.status).toBe(200);
    expect(rewriteOf(response)).toBeNull();
    expect(response.headers.get("content-security-policy")).toContain("'nonce-");
  });
});
