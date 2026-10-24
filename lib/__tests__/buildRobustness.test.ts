import { describe, expect, it } from "vitest";
import { readFileSync, readdirSync } from "node:fs";
import path from "node:path";

const root = path.resolve(__dirname, "../..");
const read = (file: string) => readFileSync(path.join(root, file), "utf8");

describe("release 2 build inputs", () => {
  it("uses repository fonts without a Google Fonts build dependency", () => {
    const layout = read("app/layout.tsx");
    expect(layout).toContain('from "next/font/local"');
    expect(layout).not.toMatch(/next\/font\/google|fonts\.googleapis|fonts\.gstatic/);
    const sources = [...layout.matchAll(/path:\s*"(\.\/fonts\/[^"]+\.woff2)"/g)];
    expect(sources).toHaveLength(6);
    for (const [, source] of sources) {
      const bytes = readFileSync(path.join(root, "app", source));
      expect(bytes.subarray(0, 4).toString()).toBe("wOF2");
    }
    const fonts = readdirSync(path.join(root, "app/fonts"));
    expect(fonts).toContain("OFL.txt");
    expect(read("app/fonts/OFL.txt")).toContain("SIL OPEN FONT LICENSE");
    expect(layout).toContain('variable: "--font-sans"');
    expect(layout).toContain('variable: "--font-mono"');
  });

  it("resolves Vitest and every mocker to the patched non-major release", () => {
    const manifest = JSON.parse(read("package.json"));
    const lock = JSON.parse(read("package-lock.json"));
    expect(manifest.devDependencies.vitest).toBe("5.0.3");
    const mockers = Object.entries(lock.packages).filter(([key]) => key.endsWith("node_modules/@vitest/mocker"));
    expect(mockers.length).toBeGreaterThan(0);
    for (const [, value] of mockers) expect((value as { version: string }).version).toBe("5.0.3");
    expect(lock.packages["node_modules/vitest"].version).toBe("5.0.3");
  });
});
