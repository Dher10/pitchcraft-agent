// Opt-in production smoke check. No external service, credential, or source request.
import assert from "node:assert/strict";
import { chromium } from "playwright";

const origin = new URL(process.argv[2] ?? "http://127.0.0.1:3082");
assert.equal(origin.protocol, "http:");
assert.ok(["localhost", "127.0.0.1", "[::1]"].includes(origin.hostname));
assert.equal(origin.pathname, "/");
const browser = await chromium.launch({ channel: "chrome", headless: true });
try {
  const context = await browser.newContext();
  const page = await context.newPage();
  const errors = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.addInitScript(() => {
    window.__violations = [];
    document.addEventListener("securitypolicyviolation", (event) => {
      window.__violations.push({ directive: event.effectiveDirective, blocked: event.blockedURI });
    });
  });
  // Vercel's intake is not served by next start. Verify the installed Analytics
  // component's real same-origin injection with a controlled endpoint stub.
  await page.route("**/_vercel/insights/script.js", (route) => route.fulfill({
    contentType: "application/javascript",
    body: "window.__analyticsLoaded = true; fetch('/_vercel/insights/view', {method:'POST'});",
  }));
  await page.route("**/_vercel/insights/view", (route) => route.fulfill({ status: 204 }));
  await page.route("**/*", (route) => {
    if (new URL(route.request().url()).origin !== origin.origin) return route.abort();
    return route.fallback();
  });
  const nonces = [];
  let staticScript;
  for (const path of ["/", "/quality", "/quality"]) {
    const response = await page.goto(new URL(path, origin).href);
    assert.equal(response.status(), 200);
    const headers = response.headers();
    assert.equal(headers["x-content-type-options"], "nosniff");
    assert.equal(headers["x-frame-options"], "DENY");
    assert.match(headers["cache-control"], /no-store/);
    const csp = headers["content-security-policy"];
    assert.ok(csp, `${path}: CSP missing`);
    const nonce = csp.match(/'nonce-([^']+)'/)?.[1];
    assert.ok(nonce, `${path}: nonce missing`);
    nonces.push(nonce);
    assert.doesNotMatch(csp.split(";").find((part) => part.trim().startsWith("script-src")), /unsafe-inline|unsafe-eval/);
    assert.match(csp, /style-src-attr 'unsafe-inline'/);
    await page.waitForFunction(() => window.__analyticsLoaded === true);
    if (path === "/") {
      await page.getByRole("button", { name: /See detailed analysis/ }).click();
      const controls = page.locator("button[aria-pressed]");
      assert.ok(await controls.count() > 1, "served fixture has interactive pitch controls");
      const target = controls.nth(1);
      await target.click();
      assert.equal(await target.getAttribute("aria-pressed"), "true");
    }
    assert.deepEqual(await page.evaluate(() => window.__violations), []);
    const scripts = await page.locator("script:not([src])").evaluateAll((nodes) => nodes.map((node) => node.nonce));
    assert.ok(scripts.length > 0);
    assert.ok(scripts.every((value) => value === nonce), "all bootstrap scripts have the response nonce");
    staticScript ??= await page.locator('script[src^="/_next/static/"]').first().getAttribute("src");
    await page.evaluate(() => {
      const node = document.createElement("div");
      node.id = "style-control";
      node.style.width = "11px";
      document.body.append(node);
    });
    assert.equal(await page.locator("#style-control").evaluate((node) => getComputedStyle(node).width), "11px");
  }
  assert.equal(new Set(nonces).size, 3);
  for (const path of ["/data/pitchcraft-demo.json", staticScript]) {
    const response = await context.request.get(new URL(path, origin).href);
    assert.equal(response.status(), 200);
    assert.equal(response.headers()["x-content-type-options"], "nosniff");
    assert.equal(response.headers()["x-frame-options"], "DENY");
    assert.match(response.headers()["content-security-policy"], /frame-ancestors 'none'/);
  }
  await page.evaluate((nonce) => {
    const inline = document.createElement("script");
    inline.textContent = "window.__unsafeInlineRan = true";
    document.body.append(inline);
    const script = document.createElement("script");
    script.src = "https://blocked.invalid/probe.js";
    document.body.append(script);
    const frame = document.createElement("iframe");
    frame.src = "https://blocked.invalid/frame";
    document.body.append(frame);
    // CDP evaluation can explicitly bypass the page's eval restriction.
    // Execute this probe in a nonce-authorized page script on a later task.
    const trusted = document.createElement("script");
    trusted.nonce = nonce;
    trusted.textContent = "setTimeout(() => { try { window.eval('window.__unsafeEvalRan = true'); } catch {} }, 0)";
    document.body.append(trusted);
  }, nonces.at(-1));
  await page.waitForFunction(() => window.__violations.length >= 4);
  assert.equal(await page.evaluate(() => window.__unsafeInlineRan || window.__unsafeEvalRan || false), false);
  const violations = await page.evaluate(() => window.__violations);
  assert.ok(violations.some((v) => v.directive === "script-src-elem" && v.blocked === "inline"));
  assert.ok(violations.some((v) => v.directive === "script-src-elem" && v.blocked.includes("blocked.invalid")));
  assert.ok(violations.some((v) => v.directive === "frame-src"));
  assert.ok(violations.some((v) => v.blocked === "eval"));
  assert.deepEqual(errors, []);
  console.log("PASS: real production responses, unique bootstrap nonces, rendering, same-origin analytics stub, styles, assets and blocked script/eval/frame probes");
} finally {
  await browser.close();
}
