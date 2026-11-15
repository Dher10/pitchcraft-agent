import { describe, expect, it } from "vitest";
import { readFileSync, readdirSync, statSync } from "node:fs";
import path from "node:path";

// P1.9 (D16) and P1.10 (D26): PitchCraft draws no ad, runs no tracker of its own and links out only to MLB, Baseball
// Savant and, since R4-U2 (D67), the two URLs of the footer: the project's repository and the author credit. The one script on the page is Vercel Web Analytics (page views only), added in app/layout.tsx.
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

// Hosts the site may name: MLB and Baseball Savant (the sources, D16), the XML namespace of an SVG, and the two outbound
// links of the footer (D67 point 1, owner 2026-11-15): the project's repository and the author credit, each only as the exact
// URL below. The credit is a plain link, never an ad, a sponsorship or a call to action.
const ALLOWED_HOSTS = [/^([a-z0-9-]+\.)*mlb\.com$/, /^www\.w3\.org$/, /^github\.com$/, /^www\.danielherdenez\.com$/];
const APPROVED_EXTERNAL_LINKS = ["https://github.com/Dher10/pitchcraft-agent", "https://www.danielherdenez.com"];
const MLB_OR_SVG = /^https?:\/\/(([a-z0-9-]+\.)*mlb\.com|www\.w3\.org)(\/|$)/i;

/** What is wrong with a link a component writes: a literal href must stay on the site; a computed one must come from the catalog. */
export function linkProblem(expression: string, file = ""): string | null {
  const literal = /^"([^"]*)"$|^'([^']*)'$/.exec(expression);
  if (literal) {
    const value = literal[1] ?? literal[2];
    // An internal path starts with one slash; "//host" is protocol-relative, and a scheme or a backslash leaves the site.
    const inside = (value.startsWith("/") && !value.startsWith("//")) || value.startsWith("#");
    return inside && !/\\|^[a-z][a-z0-9+.-]*:/i.test(value) ? null : `literal href outside the site: ${value}`;
  }
  if (/^\{SITE_COPY\.links\.\w+\}$/.test(expression)) return null; // the catalog holds the approved URLs, checked above
  // An internal path built from an id: `/segment/${id}`, never a template that starts with an interpolation.
  if (/^\{`\/[a-z][a-z-]*\/\$\{[^}`]*\}`\}$/.test(expression)) return null;
  if (/^\{(props\.)?href\}$/.test(expression)) return null; // Button: its callers' hrefs are checked at their own call
  // The archive's links are built by lib/archiveQuery.ts from validated values and always start with "/archive"
  // (lib/__tests__/archiveQuery.test.ts checks every link the calendar and the filters can make).
  if (file.startsWith("components/archive/")) {
    if (/^\{hrefFor\(/.test(expression)) return null;
    if (/^\{(calendar\.(previous|next)|cell\.href)\}$/.test(expression)) return null;
  }
  return `href not from the catalog or an internal path: ${expression}`;
}

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

  it("links out only to MLB, the SVG namespace and the two approved footer URLs, each exactly", () => {
    const urls = new Set<string>();
    for (const file of FILES) {
      for (const match of read(file).matchAll(/https?:\/\/[^\s"'`)<>]+/g)) {
        if (!MLB_OR_SVG.test(match[0])) urls.add(match[0]);
      }
    }

    expect([...urls].sort()).toEqual([...APPROVED_EXTERNAL_LINKS].sort());
  });

  it("writes only links that stay on the site or come from the catalog of approved URLs", () => {
    const problems: string[] = [];
    for (const file of FILES.filter((f) => f.endsWith(".tsx"))) {
      for (const match of read(file).matchAll(/href\s*=\s*(\{`[^`]*`\}|\{[^}]*\}|"[^"]*"|'[^']*')/g)) {
        const problem = linkProblem(match[1], rel(file));
        if (problem) problems.push(`${rel(file)}: ${problem}`);
      }
    }

    expect(problems).toEqual([]);
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

  it.each([
    ['"https://evil.example"', true],
    ['"http://www.danielherdenez.com.evil.example"', true],
    ["{url}", true],
    ["{`https://x.example/${id}`}", true],
    ["{SITE_COPY.links.author}", false],
    ["{hrefFor(query, { page: 2 }@components/archive/ArchiveView.tsx", false],
    ["{evil.href}@components/archive/Calendar.tsx", true],
    ["{hrefFrom(query)}", true],
    ["{`/game/${id}`}", false],
    ['"//ads.example.net/x"', true],
    ['{cell.href}@components/game/Other.tsx', true],
    ['{cell.href}@components/archive/Calendar.tsx', false],
    ['{hrefFor(query, {})}@components/ui/Other.tsx', true],
    ['"/\\ads.example.net"', true],
    ['"javascript:alert(1)"', true],
    ["{`/${host}/x`}", true],
    ["{`//${host}`}", true],
    ['"/archive"', false],
    ['"#how-pitchcraft-works"', false],
  ])("the link scanner judges href=%s (a problem: %s)", (expression, problem) => {
    const [expr, file] = expression.split("@");
    expect(linkProblem(expr, file ?? "") !== null).toBe(problem);
  });

  it("the external-link scanner would catch a third host", () => {
    const text = 'a https://github.com/Dher10/pitchcraft-agent b https://www.danielherdenez.com c https://ads.example.net/x';
    const urls = [...text.matchAll(/https?:\/\/[^\s"'`)<>]+/g)].map((m) => m[0]).filter((u) => !MLB_OR_SVG.test(u));
    expect(urls.sort()).not.toEqual([...APPROVED_EXTERNAL_LINKS].sort());
  });

  it.each(["baseballsavant.mlb.com", "statsapi.mlb.com", "www.mlb.com", "www.w3.org", "github.com", "www.danielherdenez.com"])("allows the host %s", (host) => {
    expect(ALLOWED_HOSTS.some((allowed) => allowed.test(host))).toBe(true);
  });

  it.each(["example.com", "mlb.com.evil.example", "notmlb.com", "ads.example.net", "evilmlb.com", "gist.github.com", "danielherdenez.com.evil.example"])("refuses the host %s", (host) => {
    expect(ALLOWED_HOSTS.some((allowed) => allowed.test(host))).toBe(false);
  });
});
