import { readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";

// D68: the app version lives in package.json and must equal the newest entry of CHANGELOG.md. The newest entry is the
// first "## [x.y.z]" heading; it may still say "Unreleased" while the owner has not merged the release.

const ROOT = process.cwd();
const read = (file: string) => readFileSync(join(ROOT, file), "utf8");

const ENTRY = /^## \[([^\]]+)\](?: - (.+))?$/gm;

function entries(changelog: string): { version: string; date: string }[] {
  return [...changelog.matchAll(ENTRY)].map((m) => ({ version: m[1], date: (m[2] ?? "").trim() }));
}

describe("entries (parser controls)", () => {
  const sample = ["# Changelog", "## [3.0.0] - Unreleased", "text", "## [2.1.0] - 2026-12-01", "## [2.0-a] - 2026-10-24"].join("\n");

  it("reads versions and dates in order, newest first", () => {
    expect(entries(sample)).toEqual([
      { version: "3.0.0", date: "Unreleased" },
      { version: "2.1.0", date: "2026-12-01" },
      { version: "2.0-a", date: "2026-10-24" },
    ]);
  });

  it("finds nothing in text without version headings", () => {
    expect(entries("# Changelog\n\nno entries here")).toEqual([]);
  });
});

describe("app version (D68)", () => {
  const log = () => entries(read("CHANGELOG.md"));
  const pkg = () => JSON.parse(read("package.json")) as { version: string };
  const lock = () =>
    JSON.parse(read("package-lock.json")) as { version: string; packages: Record<string, { version?: string }> };

  it("CHANGELOG.md has at least one entry", () => {
    expect(log().length).toBeGreaterThan(0);
  });

  it("package.json version equals the newest CHANGELOG entry", () => {
    expect(pkg().version).toBe(log()[0]?.version);
  });

  it("the newest entry is a plain MAJOR.MINOR.PATCH", () => {
    expect(log()[0]?.version).toMatch(/^\d+\.\d+\.\d+$/);
  });

  it("package-lock.json carries the same version twice", () => {
    expect(lock().version).toBe(pkg().version);
    expect(lock().packages[""].version).toBe(pkg().version);
  });

  it("every entry has a date or the word Unreleased, and only the newest may be Unreleased", () => {
    for (const e of log()) expect(e.date).toMatch(/^(Unreleased|\d{4}-\d{2}-\d{2})$/);
    expect(log().slice(1).some((e) => e.date === "Unreleased")).toBe(false);
  });
});
