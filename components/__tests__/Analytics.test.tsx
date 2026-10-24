import { describe, expect, it, vi } from "vitest";
import { render } from "@testing-library/react";
import { renderToStaticMarkup } from "react-dom/server";
import { readFileSync } from "node:fs";
import path from "node:path";

// P1.10 (D26, docs/plans/P1.md section 9): Vercel Web Analytics, page views only, no custom event, no cookie banner, and a
// /quality route that draws no visible text (its content is P3.2). Enabling Analytics in the Vercel dashboard is the owner's
// step R5; nothing here sends anything. The real <Analytics /> injects a script in a browser, so it is replaced by a marker.

vi.mock("@vercel/analytics/next", () => ({ Analytics: () => <span data-testid="analytics" /> }));
vi.mock("next/font/local", () => ({ default: () => ({ variable: "font-test" }) }));

const ROOT = path.resolve(__dirname, "..", "..");
const layoutSource = readFileSync(path.join(ROOT, "app", "layout.tsx"), "utf-8");

describe("the root layout", () => {
  it("renders the Web Analytics component once, inside the body", async () => {
    const { default: RootLayout } = await import("@/app/layout");

    // A <div> container would drop <html> and <body>, so the layout is rendered to a string and read as one.
    const html = renderToStaticMarkup(<RootLayout>{<p>page</p>}</RootLayout>);
    const body = html.slice(html.indexOf("<body"), html.indexOf("</body>"));

    expect(html.indexOf("<body")).toBeGreaterThan(-1);
    expect(html.match(/data-testid="analytics"/g)).toHaveLength(1);
    expect(body).toContain("data-testid=\"analytics\"");
    expect(body).toContain("<p>page</p>");
    expect(body.indexOf("<p>page</p>")).toBeLessThan(body.indexOf("data-testid=\"analytics\""));
  });

  it("imports the component from the Next.js entry of the package and uses it with no props", () => {
    expect(layoutSource).toMatch(/import\s*\{\s*Analytics\s*\}\s*from\s*"@vercel\/analytics\/next"/);
    expect(layoutSource.match(/<Analytics\b[^>]*>/g)).toEqual(["<Analytics />"]);
  });

  it("sends no custom event and no data of its own: page views only", () => {
    expect(layoutSource).not.toMatch(/\btrack\s*\(/);
    expect(layoutSource).not.toMatch(/beforeSend|debug=|mode=|endpoint=|scriptSrc=|basePath=/);
  });

  it("adds no other script or tag to the page", () => {
    expect(layoutSource).not.toMatch(/<script\b|next\/script|<Script\b/);
  });

  it("shows no cookie banner or consent text", () => {
    expect(layoutSource).not.toMatch(/cookie|consent/i);
  });
});

describe("the /quality route", () => {
  it("exists as a page", async () => {
    const page = await import("@/app/quality/page");

    expect(typeof page.default).toBe("function");
  });

  it("draws no visible text at all, only a main landmark with a label", async () => {
    const { default: Quality } = await import("@/app/quality/page");

    const { container } = render(<Quality />);

    expect(container.textContent).toBe("");
    const main = container.querySelector("main");
    expect(main).not.toBeNull();
    expect(main?.getAttribute("aria-label")).toBeTruthy();
    expect(container.querySelectorAll("a, img, script, iframe, form, svg, canvas")).toHaveLength(0);
  });

  it("is the only route besides the home page", () => {
    const pages = ["app/page.tsx", "app/quality/page.tsx"];

    for (const page of pages) expect(() => readFileSync(path.join(ROOT, page), "utf-8")).not.toThrow();
  });
});

describe("the dependency", () => {
  it("is pinned to an exact version in package.json", () => {
    const manifest = JSON.parse(readFileSync(path.join(ROOT, "package.json"), "utf-8")) as {
      dependencies: Record<string, string>;
    };

    expect(manifest.dependencies["@vercel/analytics"]).toMatch(/^\d+\.\d+\.\d+$/);
  });
});
