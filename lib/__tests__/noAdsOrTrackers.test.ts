import { describe, expect, it } from "vitest";
import { readFileSync, readdirSync, statSync } from "node:fs";
import path from "node:path";

// P1.9 (D16) and P1.10 (D26): PitchCraft draws no ad, runs no tracker of its own and links out only to MLB and Baseball
// Savant. The one script on the page is Vercel Web Analytics (page views only), added in app/layout.tsx.
// This reads the source of the site; it checks what is written, not what a browser does.

const ROOT = path.resolve(__dirname, "..", "..");
const FOLDERS = ["app", "components", "lib"];

function sources(folder: string): string[] {
  const found: string[] = [];
  for (const name of readdirSync(folder)) {
    const full = path.join(folder, name);
    if (name === "__tests__" || name === "node_modules") continue;
    if (statSync(full).isDirectory()) found.push(...sources(full));
    else if (/\.(ts|tsx|css)$/.test(name)) found.push(full);
  }
  return found;
}

const FILES = FOLDERS.flatMap((folder) => sources(path.join(ROOT, folder)));
const read = (file: string) => readFileSync(file, "utf-8");
const rel = (file: string) => path.relative(ROOT, file).split(path.sep).join("/");

const FORBIDDEN = [
  /<script\b/i,
  /<iframe\b/i,
  /dangerouslySetInnerHTML/,
  /from\s+["']next\/script["']/,
  /adsbygoogle|googletag|doubleclick|googlesyndication|adsense/i,
  /\bgtag\s*\(|\bfbq\s*\(|\b_paq\b|\bdataLayer\b/,
  /mixpanel|hotjar|clarity\.ms|segment\.(com|io)|amplitude|posthog|fullstory|sentry\.io/i,
];

// Hosts the site may name: MLB and Baseball Savant (the sources, D16), and the XML namespace of an SVG.
const ALLOWED_HOSTS = [/^([a-z0-9-]+\.)*mlb\.com$/, /^www\.w3\.org$/];

describe("the site's own source", () => {
  it("reads at least the app, the components and the lib", () => {
    expect(FILES.some((file) => rel(file) === "app/layout.tsx")).toBe(true);
    expect(FILES.some((file) => rel(file).startsWith("components/"))).toBe(true);
    expect(FILES.some((file) => rel(file).startsWith("lib/"))).toBe(true);
  });

  it.each(FORBIDDEN.map((pattern) => [String(pattern), pattern] as const))("has nothing that matches %s", (_name, pattern) => {
    const hits = FILES.filter((file) => pattern.test(read(file))).map(rel);

    expect(hits).toEqual([]);
  });

  it("names no host other than MLB, Baseball Savant and the SVG namespace", () => {
    const outside: string[] = [];
    for (const file of FILES) {
      for (const match of read(file).matchAll(/https?:\/\/([^\s/"'`)<>]+)/g)) {
        const host = match[1].toLowerCase();
        if (!ALLOWED_HOSTS.some((allowed) => allowed.test(host))) outside.push(`${rel(file)}: ${host}`);
      }
    }

    expect(outside).toEqual([]);
  });

  it("has no href at all (the page links nowhere)", () => {
    const links: string[] = [];
    for (const file of FILES.filter((f) => f.endsWith(".tsx"))) {
      for (const match of read(file).matchAll(/href\s*=\s*(\{[^}]*\}|"[^"]*"|'[^']*')/g)) links.push(`${rel(file)}: ${match[1]}`);
    }

    expect(links).toEqual([]);
  });

  it("imports the analytics package only in the root layout", () => {
    const importers = FILES.filter((file) => /@vercel\/analytics/.test(read(file))).map(rel);

    expect(importers).toEqual(["app/layout.tsx"]);
  });
});

describe("the dependencies", () => {
  const manifest = JSON.parse(readFileSync(path.join(ROOT, "package.json"), "utf-8")) as {
    dependencies?: Record<string, string>;
    devDependencies?: Record<string, string>;
  };
  const names = Object.keys({ ...manifest.dependencies, ...manifest.devDependencies });

  it("hold no ad, analytics or tracking package except Vercel Web Analytics", () => {
    const suspicious = names.filter((name) =>
      /analytics|gtag|segment|mixpanel|amplitude|posthog|hotjar|sentry|adsense|(^|[-/@])ads?($|[-/])|tracking|pixel/i.test(name),
    );

    expect(suspicious.filter((name) => name !== "@vercel/analytics")).toEqual([]);
  });

  it("pin @vercel/analytics to an exact version", () => {
    const version = { ...manifest.dependencies }["@vercel/analytics"];

    expect(version).toMatch(/^\d+\.\d+\.\d+$/);
  });
});

// The scanners above must be able to fail: every alternative of every pattern fires on a sample of the thing it forbids.
describe("the scanners themselves", () => {
  const BAD = [
    '<script src="https://cdn.example.com/x.js"></script>',
    '<iframe src="https://ads.example.com"></iframe>',
    "<div dangerouslySetInnerHTML={{ __html: text }} />",
    'import Script from "next/script";',
    '<ins className="adsbygoogle" />',
    "googletag.cmd.push(fn);",
    '<link href="//stats.g.doubleclick.net/x" />',
    "const pagead = 'googlesyndication.com';",
    "adsense.load()",
    "gtag('config', 'G-XXXX');",
    "fbq('track', 'PageView');",
    "_paq.push(['trackPageView']);",
    "window.dataLayer = [];",
    "mixpanel.track('view');",
    "hotjar.init(1)",
    "load('https://www.clarity.ms/tag')",
    "load('https://cdn.segment.com/analytics.js')",
    "load('https://cdn.segment.io/analytics.js')",
    "amplitude.getInstance()",
    "posthog.capture('x')",
    "fullstory.init()",
    "Sentry.init({ dsn: 'https://x@o1.ingest.sentry.io/1' })",
  ];

  // One sample per alternative of every pattern above (a deleted alternative fails here).
  it.each(BAD)("a forbidden pattern matches %s", (sample) => {
    expect(FORBIDDEN.some((pattern) => pattern.test(sample))).toBe(true);
  });

  it("control: ordinary component code matches none", () => {
    expect(FORBIDDEN.some((pattern) => pattern.test("export default function Hero() { return <section>Games</section>; }"))).toBe(false);
  });

  it.each(["baseballsavant.mlb.com", "statsapi.mlb.com", "www.mlb.com", "www.w3.org"])("allows the host %s", (host) => {
    expect(ALLOWED_HOSTS.some((allowed) => allowed.test(host))).toBe(true);
  });

  it.each(["example.com", "mlb.com.evil.example", "notmlb.com", "ads.example.net", "evilmlb.com"])("refuses the host %s", (host) => {
    expect(ALLOWED_HOSTS.some((allowed) => allowed.test(host))).toBe(false);
  });
});
