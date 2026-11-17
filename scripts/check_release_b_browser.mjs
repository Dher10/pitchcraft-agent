// Opt-in browser checks of release B against a local production build (`npm run build`, then `npx next start -p 3082`).
// No external service, credential or source request. Usage:
//   node scripts/check_release_b_browser.mjs [origin] [check ...]
// Checks: csp (the archive team form submits with JavaScript off and logs no CSP violation).
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { chromium } from "playwright";

const origin = new URL(process.argv[2] ?? "http://127.0.0.1:3082");
assert.equal(origin.protocol, "http:");
assert.ok(["localhost", "127.0.0.1", "[::1]"].includes(origin.hostname));
assert.equal(origin.pathname, "/");
const ALL = ["csp"];
const wanted = process.argv.slice(3);
const checks = wanted.length > 0 ? wanted : ALL;
for (const check of checks) assert.ok(ALL.includes(check), `unknown check: ${check}`);

const index = JSON.parse(readFileSync(new URL("../public/data/archive/index-2026.json", import.meta.url), "utf8"));
const url = (path) => new URL(path, origin).href;

/** A page with JavaScript off whose browser log (CSP violations included) is collected over CDP. */
async function pageWithoutJs(browser, viewport) {
  const context = await browser.newContext({ javaScriptEnabled: false, viewport });
  await context.route("**/*", (route) =>
    new URL(route.request().url()).origin === origin.origin ? route.fallback() : route.abort(),
  );
  const page = await context.newPage();
  const log = [];
  const cdp = await context.newCDPSession(page);
  cdp.on("Log.entryAdded", ({ entry }) => log.push(entry));
  await cdp.send("Log.enable");
  return { context, page, log };
}

const cspViolations = (log) => log.filter((entry) => /Content Security Policy/i.test(entry.text));

/** The game ids linked from the results (rows on a phone, the table from 1024 px). */
async function resultGames(page) {
  const hrefs = await page.locator("[data-results] a[href^='/game/']").evaluateAll((nodes) => nodes.map((n) => n.getAttribute("href")));
  return [...new Set(hrefs.map((href) => Number(href.split("/").at(-1))))].sort((a, b) => a - b);
}

async function checkCsp(browser) {
  const expected = index.games
    .filter((row) => row.away.abbreviation === "MIL" || row.home.abbreviation === "MIL")
    .map((row) => row.game_pk)
    .sort((a, b) => a - b);
  assert.ok(expected.length > 0 && expected.length < index.games.length, "MIL is a strict subset of the archive");
  for (const viewport of [{ width: 375, height: 812 }, { width: 1280, height: 900 }]) {
    const { context, page, log } = await pageWithoutJs(browser, viewport);
    try {
      const response = await page.goto(url("/archive"));
      assert.equal(response.status(), 200);
      await page.selectOption("#archive-team", "MIL");
      await page.locator("form[action='/archive'] button[type='submit']").click({ noWaitAfter: true });
      await page.waitForURL((target) => target.searchParams.get("team") === "MIL", { timeout: 5000 }).catch(() => {});
      assert.deepEqual(cspViolations(log), [], `${viewport.width}px: no CSP violation`);
      assert.equal(new URL(page.url()).searchParams.get("team"), "MIL", `${viewport.width}px: the form submitted`);
      assert.deepEqual(await resultGames(page), expected, `${viewport.width}px: only the MIL games are listed`);
      assert.match(response.headers()["content-security-policy"], /form-action 'self'/);
      console.log(`csp ${viewport.width}px: /archive?team=MIL lists ${expected.length} games (all MIL), no CSP violation, JavaScript off`);
    } finally {
      await context.close();
    }
  }
}

const browser = await chromium.launch({ channel: "chrome", headless: true });
try {
  if (checks.includes("csp")) await checkCsp(browser);
  console.log(`PASS: ${checks.join(", ")}`);
} finally {
  await browser.close();
}
