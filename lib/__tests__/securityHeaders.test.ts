// @vitest-environment node
import { describe, expect, it } from "vitest";
import { NextRequest } from "next/server";

describe("P2-SEC response boundary", () => {
  it("overwrites client nonce/CSP and uses a fresh nonce on every request", async () => {
    const { proxy } = await import("../../proxy");
    const request = new NextRequest("http://localhost/quality", {
      headers: { "x-nonce": "attacker", "content-security-policy": "script-src *" },
    });
    const first = proxy(request);
    const second = proxy(request);
    const policy = first.headers.get("content-security-policy")!;
    const nonce = policy.match(/'nonce-([^']+)'/)![1];
    expect(nonce).toMatch(/^[A-Za-z0-9+/]{32}$/);
    expect(second.headers.get("content-security-policy")).not.toBe(policy);
    expect(policy).not.toContain("attacker");
    expect(first.headers.get("x-middleware-request-x-nonce")).toBe(nonce);
    expect(first.headers.get("x-middleware-request-content-security-policy")).toBe(policy);
  });

  it("permits same-origin analytics and existing styles without enabling inline/eval scripts", async () => {
    const { proxy } = await import("../../proxy");
    const policy = proxy(new NextRequest("http://localhost/")).headers.get("content-security-policy")!;
    const directives = Object.fromEntries(policy.split(";").filter(Boolean).map((part) => {
      const [name, ...values] = part.trim().split(/\s+/);
      return [name, values];
    }));
    expect(directives["script-src"]).toHaveLength(2);
    expect(directives["script-src"][0]).toBe("'self'");
    expect(directives["script-src"].join(" ")).not.toMatch(/unsafe-inline|unsafe-eval|\*/);
    expect(directives["connect-src"]).toEqual(["'self'"]);
    expect(directives["style-src-attr"]).toEqual(["'unsafe-inline'"]);
    expect(directives["frame-ancestors"]).toEqual(["'none'"]);
    expect(directives["frame-src"]).toEqual(["'none'"]);
    expect(directives["object-src"]).toEqual(["'none'"]);
    expect(policy).not.toMatch(/https?:|unsafe-eval/);
  });

  // Codex audit of PR #6 (2026-11-17): with JavaScript off, the archive's team form (a plain GET to /archive) was blocked by
  // form-action 'none'. Owner's decision: form-action 'self' and nothing else in the document policy changes.
  it("lets same-origin forms submit and keeps every other directive as it was", async () => {
    const { proxy } = await import("../../proxy");
    const policy = proxy(new NextRequest("http://localhost/archive")).headers.get("content-security-policy")!;
    const directives = policy.split(";").map((part) => part.trim().replace(/'nonce-[^']+'/, "'nonce'"));
    expect(directives).toEqual([
      "default-src 'self'",
      "script-src 'self' 'nonce'",
      "style-src 'self' 'nonce'",
      "style-src-attr 'unsafe-inline'",
      "connect-src 'self'",
      "font-src 'self'",
      "img-src 'self' data:",
      "object-src 'none'",
      "frame-src 'none'",
      "frame-ancestors 'none'",
      "base-uri 'self'",
      "form-action 'self'",
    ]);
  });

  it("sets no-cache on documents and nosniff/frame protection on all resources", async () => {
    const { proxy } = await import("../../proxy");
    const response = proxy(new NextRequest("http://localhost/quality"));
    expect(response.headers.get("cache-control")).toContain("no-store");
    const { default: config } = await import("../../next.config");
    const rules = await config.headers!();
    const all = rules.find((rule) => rule.source === "/:path*")!;
    expect(all.headers).toContainEqual({ key: "X-Content-Type-Options", value: "nosniff" });
    expect(all.headers).toContainEqual({ key: "X-Frame-Options", value: "DENY" });
    for (const source of ["/data/:path*", "/_next/static/:path*", "/favicon.ico"]) {
      const resource = rules.find((rule) => rule.source === source);
      expect(resource?.headers.find((h) => h.key === "Content-Security-Policy")?.value).toContain("frame-ancestors 'none'");
    }
  });
});
