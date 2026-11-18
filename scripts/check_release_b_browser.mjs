// Opt-in browser checks of release B against a local production build (`npm run build`, then `npx next start -p 3082`).
// No external service, credential or source request. Usage:
//   node scripts/check_release_b_browser.mjs [origin] [check ...]
// Checks: csp (the archive team form submits with JavaScript off and logs no CSP violation);
//         targets (every interactive element of the release B pages is at least 44x44 px, none overlap, no sideways
//         scroll, at 375, 430 and 1280 px);
//         notfound (with JavaScript off, an unknown and a malformed game id are a 404 whose HTML has the heading and the
//         recovery links; a published game is a 200 with its page; release 2.1.1).
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { chromium } from "playwright";

const origin = new URL(process.argv[2] ?? "http://127.0.0.1:3082");
assert.equal(origin.protocol, "http:");
assert.ok(["localhost", "127.0.0.1", "[::1]"].includes(origin.hostname));
assert.equal(origin.pathname, "/");
const ALL = ["csp", "targets", "notfound"];
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

async function checkNotFound(browser) {
  const { context, page, log } = await pageWithoutJs(browser, { width: 375, height: 812 });
  try {
    for (const id of ["123", "abc"]) {
      const response = await page.goto(url(`/game/${id}`));
      assert.equal(response.status(), 404, `/game/${id}: status`);
      const html = await response.text();
      assert.match(html, /<h1[^>]*>We could not find that game<\/h1>/, `/game/${id}: the heading is in the server's HTML`);
      assert.match(html, /<a[^>]*href="\/archive"[^>]*>[^<]*Back to the archive/, `/game/${id}: the archive link`);
      assert.match(html, /<a[^>]*href="\/notable"[^>]*>[^<]*Notable duels of 2026/, `/game/${id}: the notable link`);
      assert.match(html, /<meta name="robots" content="noindex/, `/game/${id}: noindex`);
      assert.match(response.headers()["content-security-policy"], /script-src 'self' 'nonce-/, `/game/${id}: the CSP`);
      assert.equal(await page.locator("h1").textContent(), "We could not find that game", `/game/${id}: the heading is shown`);
      console.log(`notfound /game/${id}: 404, heading and both links in the HTML, noindex, JavaScript off`);
    }
    const game = index.games[0].game_pk;
    const response = await page.goto(url(`/game/${game}`));
    assert.equal(response.status(), 200, `/game/${game}: status`);
    // The game page's flight data carries its not-found boundary, so the check is on the rendered heading, not the raw HTML.
    assert.equal(await page.locator("h1").count(), 1, `/game/${game}: one heading`);
    assert.notEqual((await page.locator("h1").textContent()).trim(), "We could not find that game", `/game/${game}: not the not-found page`);
    assert.equal(await page.locator("main").first().isVisible(), true, `/game/${game}: the page renders`);
    console.log(`notfound /game/${game}: 200 with the game page (h1 "${(await page.locator("h1").textContent()).trim()}"), JavaScript off`);
    assert.deepEqual(cspViolations(log), [], "no CSP violation");
  } finally {
    await context.close();
  }
}

const TARGET = 44;
const WIDTHS = [375, 430, 1280];

/** The nine page states of release B, from the published index. */
function releaseBPages() {
  const published = index.games.find((row) => row.report.origin === "published_live");
  const reconstructed = index.games.find((row) => row.report.origin === "reconstructed");
  const days = [...new Set(index.games.map((row) => row.date))].sort();
  const mil = index.games.filter((row) => row.away.abbreviation === "MIL" || row.home.abbreviation === "MIL").map((row) => row.date);
  const absent = days.find((day) => !mil.includes(day));
  return [
    "/",
    `/game/${published.game_pk}`,
    `/game/${reconstructed.game_pk}`,
    "/notable",
    "/notable?reason=strikeout_duel",
    "/archive",
    `/archive?from=${days.at(-4)}&to=${days.at(-1)}`,
    `/archive?team=MIL&from=${absent}`,
    "/game/123",
  ];
}

/** Every visible interactive element, its box, and whether the page scrolls sideways. Runs in the page. */
function measure() {
  const selector = "a[href], button, select, textarea, summary, input:not([type='hidden']), [role='button'], [tabindex]:not([tabindex='-1'])";
  // Rendered and reachable: not display:none, not visibility:hidden, not inside a closed <details> (content-visibility).
  const visible = (node) => {
    const box = node.getBoundingClientRect();
    return node.checkVisibility({ checkVisibilityCSS: true, contentVisibilityAuto: true }) && box.width > 1 && box.height > 1;
  };
  const describe = (node) => {
    const label = node.getAttribute("aria-label") || node.textContent.trim().replace(/\s+/g, " ").slice(0, 40);
    return `${node.tagName.toLowerCase()}${node.getAttribute("href") ? `[href=${node.getAttribute("href")}]` : ""} "${label}"`;
  };
  // The area that takes the tap: the element's box, grown by an absolutely positioned ::before or ::after that the element
  // contains (a small icon button can carry a 44 px hit area that way).
  const hitArea = (node) => {
    const box = node.getBoundingClientRect();
    let [left, top, right, bottom] = [box.left, box.top, box.right, box.bottom];
    if (getComputedStyle(node).position !== "static") {
      for (const pseudo of ["::before", "::after"]) {
        const style = getComputedStyle(node, pseudo);
        if (style.content === "none" || style.position !== "absolute") continue;
        const inset = ["left", "top", "right", "bottom"].map((side) => (style[side].endsWith("px") ? parseFloat(style[side]) : null));
        if (inset.some((value) => value === null)) continue;
        left = Math.min(left, box.left + inset[0]);
        top = Math.min(top, box.top + inset[1]);
        right = Math.max(right, box.right - inset[2]);
        bottom = Math.max(bottom, box.bottom - inset[3]);
      }
    }
    return { x: left + scrollX, y: top + scrollY, width: right - left, height: bottom - top };
  };
  const targets = [...document.querySelectorAll(selector)].filter(visible).map((node) => ({ what: describe(node), ...hitArea(node) }));
  return { targets, scrollWidth: document.documentElement.scrollWidth, innerWidth };
}

async function checkTargets(browser) {
  const problems = [];
  let measured = 0;
  for (const width of WIDTHS) {
    const context = await browser.newContext({ viewport: { width, height: 900 } });
    await context.route("**/*", (route) =>
      new URL(route.request().url()).origin === origin.origin ? route.fallback() : route.abort(),
    );
    const page = await context.newPage();
    try {
      for (const path of releaseBPages()) {
        await page.goto(url(path));
        await page.waitForLoadState("networkidle");
        // As loaded, then with every <details> open, so rows behind "show all" are measured once they can be tapped.
        for (const state of ["loaded", "details open"]) {
          if (state === "details open") await page.evaluate(() => document.querySelectorAll("details").forEach((d) => { d.open = true; }));
          const where = `${width}px ${path}${state === "loaded" ? "" : " (details open)"}`;
          const { targets, scrollWidth, innerWidth } = await page.evaluate(measure);
          measured += targets.length;
          if (scrollWidth > innerWidth) problems.push(`${where}: sideways scroll (${scrollWidth} > ${innerWidth})`);
          for (const t of targets) {
            if (t.width < TARGET - 0.01 || t.height < TARGET - 0.01) {
              problems.push(`${where}: ${t.what} is ${t.width.toFixed(1)}x${t.height.toFixed(1)}`);
            }
          }
          for (let i = 0; i < targets.length; i += 1) {
            for (let j = i + 1; j < targets.length; j += 1) {
              const a = targets[i];
              const b = targets[j];
              const w = Math.min(a.x + a.width, b.x + b.width) - Math.max(a.x, b.x);
              const h = Math.min(a.y + a.height, b.y + b.height) - Math.max(a.y, b.y);
              if (w > 0.5 && h > 0.5) problems.push(`${where}: ${a.what} overlaps ${b.what}`);
            }
          }
        }
      }
    } finally {
      await context.close();
    }
  }
  assert.ok(measured > 0, "measured some targets");
  assert.deepEqual(problems, [], `${problems.length} target problems`);
  console.log(`targets: ${measured} interactive elements on ${releaseBPages().length} pages at ${WIDTHS.join(", ")} px, all at least ${TARGET}x${TARGET}, none overlapping, no sideways scroll`);
}

const browser = await chromium.launch({ channel: "chrome", headless: true });
try {
  if (checks.includes("csp")) await checkCsp(browser);
  if (checks.includes("targets")) await checkTargets(browser);
  if (checks.includes("notfound")) await checkNotFound(browser);
  console.log(`PASS: ${checks.join(", ")}`);
} finally {
  await browser.close();
}
