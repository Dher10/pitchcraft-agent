import { readdirSync, readFileSync, existsSync, statSync } from "node:fs";
import { join, relative } from "node:path";
import { describe, expect, it } from "vitest";

/**
 * U1 of release B (docs/plans/R4-U.md): the design tokens are in the build and four guards keep the old
 * habits out. A guard counts violations per file; a file that is not in its exception table must have none, and a
 * file that is in it must have exactly the listed count. A count that went down fails until the table is lowered,
 * so the tables only shrink. The unit that replaces a component removes its row.
 */

const ROOT = process.cwd();

function read(path: string): string {
  return readFileSync(join(ROOT, path), "utf8");
}

// ---------------------------------------------------------------------------------------------------------------
// What each guard looks for. Pure functions over text, so a planted violation can prove the guard sees it.
// ---------------------------------------------------------------------------------------------------------------

const LIGHT_TEXT = /\btext-(?:neutral|slate|gray|zinc|stone)-(?:50|100|200|300|400)\b/g;
const ARBITRARY_TEXT = /\btext-\[[0-9.]+(?:px|rem|em)\]/g;
const HEX = /#[0-9a-fA-F]{3}(?:[0-9a-fA-F]{3}(?:[0-9a-fA-F]{2})?|[0-9a-fA-F])?\b/g;

function toPixels(value: number, unit: string): number {
  return unit === "px" ? value : value * 16;
}

export function lightTextUses(text: string): number {
  return (text.match(LIGHT_TEXT) ?? []).length;
}

export function arbitraryTextSizes(text: string): number {
  return (text.match(ARBITRARY_TEXT) ?? []).length;
}

/** Text smaller than 12 px: an arbitrary class, a `fontSize` prop or object key, or a `font-size` declaration. */
export function textUnder12px(text: string): number {
  let count = 0;
  for (const m of text.matchAll(/\btext-\[([0-9.]+)(px|rem|em)\]/g)) {
    if (toPixels(Number(m[1]), m[2]) < 12) count += 1;
  }
  for (const m of text.matchAll(/\bfontSize\s*[:=]\s*\{?\s*([0-9.]+)\b/g)) {
    if (Number(m[1]) < 12) count += 1;
  }
  for (const m of text.matchAll(/\bfont-size\s*:\s*([0-9.]+)(px|rem|em)\b/g)) {
    if (toPixels(Number(m[1]), m[2]) < 12) count += 1;
  }
  return count;
}

/** The part of globals.css that is not a token definition: the `@theme` blocks are where hex literals may live. */
export function withoutThemeBlocks(css: string): string {
  let out = "";
  let i = 0;
  while (i < css.length) {
    const at = css.indexOf("@theme", i);
    if (at === -1) {
      out += css.slice(i);
      break;
    }
    out += css.slice(i, at);
    const open = css.indexOf("{", at);
    let depth = 1;
    let j = open + 1;
    while (j < css.length && depth > 0) {
      if (css[j] === "{") depth += 1;
      else if (css[j] === "}") depth -= 1;
      j += 1;
    }
    i = j;
  }
  return out;
}

export function hexLiterals(text: string): number {
  return (text.match(HEX) ?? []).length;
}

// ---------------------------------------------------------------------------------------------------------------
// The files the guards read.
// ---------------------------------------------------------------------------------------------------------------

function sourceFiles(dir: string): string[] {
  const found: string[] = [];
  for (const entry of readdirSync(join(ROOT, dir))) {
    if (["__tests__", "node_modules", ".next", "fonts"].includes(entry)) continue;
    const path = join(dir, entry);
    if (statSync(join(ROOT, path)).isDirectory()) found.push(...sourceFiles(path));
    else if (/\.(tsx?|css)$/.test(entry) && !/\.test\./.test(entry)) found.push(path.replaceAll("\\", "/"));
  }
  return found;
}

const APP_AND_COMPONENTS = [...sourceFiles("app"), ...sourceFiles("components")];

function counts(files: string[], count: (text: string, file: string) => number): Record<string, number> {
  const found: Record<string, number> = {};
  for (const file of files) {
    const n = count(read(file), file);
    if (n > 0) found[file] = n;
  }
  return found;
}

/** Fails with the table to paste when the counts differ from the exceptions; the tables only shrink. */
function expectOnlyTheExceptions(found: Record<string, number>, exceptions: Record<string, number>) {
  expect(found).toEqual(exceptions);
}

// ---------------------------------------------------------------------------------------------------------------
// Exceptions: components of the old design that a later unit replaces. A row is removed by that unit.
// ---------------------------------------------------------------------------------------------------------------

// A `text-[11px]` counts in the under-12px table and in the arbitrary-size table: the two rules are separate on purpose.
const TEXT_UNDER_12PX_EXCEPTIONS: Record<string, number> = {
  "components/AgentPipeline.tsx": 2,
  "components/ArchiveTable.tsx": 1,
  "components/CallCheck.tsx": 1,
  "components/CriticReviewPanel.tsx": 3,
  "components/DetailedAnalysis.tsx": 5,
  "components/Disclaimer.tsx": 2,
  "components/GameCarousel.tsx": 4,
  "components/Hero.tsx": 1,
  "components/MatchupView.tsx": 8,
  "components/ModeLine.tsx": 1,
  "components/PitchTrajectoryCard.tsx": 4,
  "components/ScoutingReport.tsx": 1,
  "components/StarterCard.tsx": 5,
  "components/StatTile.tsx": 1,
  "components/StrengthProfile.tsx": 3,
};
const LIGHT_TEXT_EXCEPTIONS: Record<string, number> = {
  "components/ArchiveTable.tsx": 1,
  "components/CriticReviewPanel.tsx": 1,
  "components/DetailedAnalysis.tsx": 3,
  "components/Disclaimer.tsx": 2,
  "components/GameCarousel.tsx": 5,
  "components/Hero.tsx": 1,
  "components/MatchupView.tsx": 4,
  "components/PitchTrajectoryCard.tsx": 2,
  "components/ScoutingReport.tsx": 1,
  "components/StarterCard.tsx": 3,
  "components/StatTile.tsx": 1,
  "components/StrengthProfile.tsx": 2,
};
const ARBITRARY_TEXT_EXCEPTIONS: Record<string, number> = {
  "components/AgentPipeline.tsx": 5,
  "components/ArchiveTable.tsx": 6,
  "components/CallCheck.tsx": 3,
  "components/CriticReviewPanel.tsx": 7,
  "components/DetailedAnalysis.tsx": 5,
  "components/Disclaimer.tsx": 2,
  "components/GameCarousel.tsx": 5,
  "components/Hero.tsx": 2,
  "components/MatchupView.tsx": 13,
  "components/ModeLine.tsx": 1,
  "components/PitchTrajectoryCard.tsx": 3,
  "components/ScoutingReport.tsx": 3,
  "components/StarterCard.tsx": 8,
  "components/StatTile.tsx": 1,
  "components/StrengthProfile.tsx": 2,
};
const HEX_EXCEPTIONS: Record<string, number> = {
  "components/PitchMixChart.tsx": 5,
  "components/PitchTrajectoryCard.tsx": 4,
  "components/StrengthProfile.tsx": 7,
  "components/VelocityChart.tsx": 5,
  "components/ZoneDiagram.tsx": 16,
};

describe("the guards see what they are for (controls)", () => {
  it("flags text under 12 px and passes 12 px and above", () => {
    expect(textUnder12px('<p className="text-[11px]">x</p>')).toBe(1);
    expect(textUnder12px('<p className="text-[0.7rem]">x</p>')).toBe(1);
    expect(textUnder12px("<Badge fontSize={9} />")).toBe(1);
    expect(textUnder12px("tick={{ fontSize: 11 }}")).toBe(1);
    expect(textUnder12px(".a { font-size: 10px; }")).toBe(1);
    expect(textUnder12px('<p className="text-[12px]">x</p>')).toBe(0);
    expect(textUnder12px("tick={{ fontSize: 12 }}")).toBe(0);
    expect(textUnder12px(".a { font-size: 0.75rem; }")).toBe(0);
    expect(textUnder12px('<p className="text-xs text-sm">x</p>')).toBe(0);
  });

  it("flags text-neutral-400 and lighter and passes text-neutral-500 and darker", () => {
    for (const cls of ["text-neutral-400", "text-neutral-300", "text-slate-400", "text-gray-200", "text-zinc-100"]) {
      expect(lightTextUses(`<p className="${cls}">x</p>`)).toBe(1);
    }
    for (const cls of ["text-neutral-500", "text-neutral-900", "text-ink-3", "text-on-board-2"]) {
      expect(lightTextUses(`<p className="${cls}">x</p>`)).toBe(0);
    }
  });

  it("flags an arbitrary text size and passes a token size", () => {
    expect(arbitraryTextSizes('<p className="text-[13px] font-bold">x</p>')).toBe(1);
    expect(arbitraryTextSizes('<p className="text-[1rem]">x</p>')).toBe(1);
    expect(arbitraryTextSizes('<p className="text-label text-body-sm text-caption">x</p>')).toBe(0);
  });

  it("flags a hex literal in any spelling and passes a token or a link anchor", () => {
    for (const hex of ["#fff", "#FFFFFF", "#1d4ed8", "#1d4ed8cc", "#abcd"]) {
      expect(hexLiterals(`<rect fill="${hex}" />`)).toBe(1);
      expect(hexLiterals(`.a { color: ${hex}; }`)).toBe(1);
    }
    expect(hexLiterals('<rect fill="var(--color-ink)" className="bg-board" />')).toBe(0);
    expect(hexLiterals('<a href="#how-it-works">x</a>')).toBe(0);
  });

  it("exempts the token definitions of globals.css and nothing else in it", () => {
    const css = `@theme { --color-ink: #0F231B; }\n@theme inline { --font-sans: var(--font-sans); }\n.a { color: #fff; }`;
    expect(hexLiterals(css)).toBe(2);
    expect(hexLiterals(withoutThemeBlocks(css))).toBe(1);
    expect(hexLiterals(withoutThemeBlocks("@theme {\n  --shadow-pop: 0 8px rgba(0,0,0,0.1);\n  --color-a: #123456;\n}\n"))).toBe(0);
  });
});

describe("the guards on the code (exceptions only shrink)", () => {
  it("no text under 12 px", () => {
    expectOnlyTheExceptions(counts(APP_AND_COMPONENTS, textUnder12px), TEXT_UNDER_12PX_EXCEPTIONS);
  });

  it("no text-neutral-400 or lighter", () => {
    expectOnlyTheExceptions(counts(APP_AND_COMPONENTS, lightTextUses), LIGHT_TEXT_EXCEPTIONS);
  });

  it("no arbitrary text-[..px] size", () => {
    expectOnlyTheExceptions(counts(APP_AND_COMPONENTS, arbitraryTextSizes), ARBITRARY_TEXT_EXCEPTIONS);
  });

  it("no hex literal in app/ and components/, except the token definitions of globals.css (owner, 2026-11-15)", () => {
    const found = counts(APP_AND_COMPONENTS, (text, file) =>
      hexLiterals(file === "app/globals.css" ? withoutThemeBlocks(text) : text),
    );
    expectOnlyTheExceptions(found, HEX_EXCEPTIONS);
  });

  it("lib/ has no hex literal either, except lib/teamColors.ts (team colors are data, not tokens)", () => {
    const lib = sourceFiles("lib").filter((file) => file !== "lib/teamColors.ts");
    expect(counts(lib, hexLiterals)).toEqual({});
    expect(hexLiterals(read("lib/teamColors.ts"))).toBeGreaterThan(0);
  });
});

// ---------------------------------------------------------------------------------------------------------------
// The tokens are in the build.
// ---------------------------------------------------------------------------------------------------------------

interface Tokens {
  color: { tokens: { name: string; value: string }[] };
  type: { groups: { styles: { name: string; fontSize: string; lineHeight: string; fontWeight: number; letterSpacing?: string }[] }[] };
  spacing: { tokens: { name: string; value: string }[] };
  radius: { tokens: { name: string; value: string }[] };
  shadow: { tokens: { name: string; value: string }[] };
  layout: { tokens: { name: string; value: string }[] };
}

const TOKENS = JSON.parse(read("docs/design/tokens.json")) as Tokens;

/** The text of every `@theme` block of globals.css, `inline` ones included. */
function themeText(): string {
  const css = read("app/globals.css");
  const blocks: string[] = [];
  let i = 0;
  while ((i = css.indexOf("@theme", i)) !== -1) {
    const open = css.indexOf("{", i);
    let depth = 1;
    let j = open + 1;
    while (j < css.length && depth > 0) {
      if (css[j] === "{") depth += 1;
      else if (css[j] === "}") depth -= 1;
      j += 1;
    }
    blocks.push(css.slice(open + 1, j - 1));
    i = j;
  }
  return blocks.join("\n");
}

function declared(theme: string, property: string): string | undefined {
  const m = theme.match(new RegExp(`(?:^|[\\s;{])${property.replace(/[-]/g, "\\-")}\\s*:\\s*([^;]+);`, "i"));
  return m?.[1].trim();
}

describe("design tokens (docs/design/tokens.json) are under @theme in app/globals.css", () => {
  const theme = themeText();

  it("has every color", () => {
    for (const token of TOKENS.color.tokens) {
      expect(declared(theme, `--color-${token.name}`)?.toLowerCase(), token.name).toBe(token.value.toLowerCase());
    }
  });

  it("has every text style with its line height, weight and letter spacing", () => {
    const styles = TOKENS.type.groups.flatMap((group) => group.styles);
    expect(styles.length).toBeGreaterThanOrEqual(13);
    for (const style of styles) {
      expect(declared(theme, `--text-${style.name}`), style.name).toBe(style.fontSize);
      expect(declared(theme, `--text-${style.name}--line-height`), style.name).toBe(style.lineHeight);
      expect(declared(theme, `--text-${style.name}--font-weight`), style.name).toBe(String(style.fontWeight));
      if (style.letterSpacing) {
        expect(declared(theme, `--text-${style.name}--letter-spacing`), style.name).toBe(style.letterSpacing);
      }
    }
  });

  it("has no text style under 12 px", () => {
    for (const style of TOKENS.type.groups.flatMap((group) => group.styles)) {
      expect(Number.parseFloat(style.fontSize), style.name).toBeGreaterThanOrEqual(12);
    }
  });

  it("has the spacing, radius, shadow, layout and breakpoint tokens", () => {
    for (const token of TOKENS.spacing.tokens) expect(declared(theme, `--spacing-${token.name}`), token.name).toBe(token.value);
    for (const token of TOKENS.radius.tokens) {
      expect(declared(theme, `--radius-${token.name.replace(/^radius-/, "")}`), token.name).toBe(token.value);
    }
    for (const token of TOKENS.shadow.tokens) expect(declared(theme, `--${token.name.replace(/^shadow-/, "shadow-")}`), token.name).toBe(token.value);
    const layout = Object.fromEntries(TOKENS.layout.tokens.map((token) => [token.name, token.value]));
    expect(declared(theme, "--container-content")).toBe(layout["content-max"]);
    expect(declared(theme, "--container-reading")).toBe(layout["reading-max"]);
    expect(declared(theme, "--spacing-tap")).toBe(layout["tap-min"]);
    expect(declared(theme, "--breakpoint-bp-md")).toBe(layout["bp-md"]);
    expect(declared(theme, "--breakpoint-bp-lg")).toBe(layout["bp-lg"]);
  });

  it("names the display and the text family, each falling back to a system face", () => {
    expect(declared(theme, "--font-display")).toMatch(/^var\(--font-display\), "Arial Narrow", sans-serif$/);
    expect(declared(theme, "--font-sans")).toMatch(/^var\(--font-sans\), .*sans-serif$/);
  });

  it("draws the focus ring from the tokens, in signal on the board", () => {
    const outside = withoutThemeBlocks(read("app/globals.css"));
    expect(outside).toMatch(/:focus-visible\s*\{[^}]*var\(--color-focus\)/);
    expect(outside).toMatch(/\[data-on-board\][^{]*:focus-visible[^{]*\{[^}]*var\(--color-signal\)/);
  });
});

describe("Big Shoulders Display, self-hosted", () => {
  const dir = "app/fonts";

  it("ships the file and its license", () => {
    expect(existsSync(join(ROOT, dir, "big-shoulders-display-latin-wght-normal.woff2"))).toBe(true);
    expect(read(`${dir}/LICENSE-big-shoulders-display.txt`)).toMatch(/SIL Open Font License,? Version 1\.1/i);
  });

  it("is loaded with next/font/local as --font-display, same origin", () => {
    const layout = read("app/layout.tsx");
    expect(layout).toContain("./fonts/big-shoulders-display-latin-wght-normal.woff2");
    expect(layout).toContain('variable: "--font-display"');
    expect(layout).toMatch(/className=\{`[^`]*\$\{bigShoulders\.variable\}/);
    expect(layout).not.toMatch(/fonts\.googleapis|fonts\.gstatic/);
  });

  it("is recorded in the fonts README with its source package", () => {
    const readme = read(`${dir}/README.md`);
    expect(readme).toContain("Big Shoulders Display");
    expect(readme).toContain("@fontsource-variable/big-shoulders-display@5.3.0");
    expect(readme).toContain("LICENSE-big-shoulders-display.txt");
  });

  it("keeps IBM Plex Mono until the unit that removes its last use (U6)", () => {
    const uses = APP_AND_COMPONENTS.filter((file) => /font-mono/.test(read(file)));
    expect(uses.length).toBeGreaterThan(0);
    expect(existsSync(join(ROOT, dir, "ibm-plex-mono-latin-500-normal.woff2"))).toBe(true);
  });
});

it("every file of the exception tables still exists", () => {
  for (const table of [TEXT_UNDER_12PX_EXCEPTIONS, LIGHT_TEXT_EXCEPTIONS, ARBITRARY_TEXT_EXCEPTIONS, HEX_EXCEPTIONS]) {
    for (const file of Object.keys(table)) expect(existsSync(join(ROOT, file)), relative(ROOT, file)).toBe(true);
  }
});
