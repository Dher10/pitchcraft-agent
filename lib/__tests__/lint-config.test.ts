import { describe, expect, it, vi } from "vitest";
import { ESLint } from "eslint";

// QA found `npm run lint` failing on Windows while it scanned .pytest_cache, a folder pytest
// creates and the OS may deny. The lint must never look at it, or at other tool caches.
// Loading the Next.js ESLint config takes several seconds the first time.
vi.setConfig({ testTimeout: 30_000 });

describe("eslint ignores", () => {
  const eslint = new ESLint();

  it.each([
    [".pytest_cache/v/cache/lastfailed.js"],
    [".pytest_cache/README.js"],
    [".next/server/app/page.js"],
  ])("does not lint %s", async (path) => {
    expect(await eslint.isPathIgnored(path)).toBe(true);
  });

  it("still lints the code", async () => {
    expect(await eslint.isPathIgnored("components/DetailedAnalysis.tsx")).toBe(false);
    expect(await eslint.isPathIgnored("lib/format.ts")).toBe(false);
  });
});
