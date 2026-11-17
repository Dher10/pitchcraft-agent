import { readFileSync } from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";
import { GLOSSARY, definitionOf } from "@/lib/glossary";

// Help text comes only from the glossary of docs/design/CONTENT.md, word for word (U2, COMPONENTS.md "Help").

function contentGlossary(): Record<string, string> {
  const text = readFileSync(path.join(process.cwd(), "docs/design/CONTENT.md"), "utf8");
  const start = text.indexOf("## Glossary");
  const rows = text
    .slice(start)
    .split("\n")
    .filter((line) => line.startsWith("|") && !line.startsWith("|---") && !line.startsWith("| Term"));
  const found: Record<string, string> = {};
  for (const row of rows) {
    const cells = row.split("|").slice(1, -1).map((cell) => cell.trim());
    found[cells[0]] = cells[1];
  }
  return found;
}

describe("the glossary", () => {
  const reference = contentGlossary();

  it("reads at least the terms of the design", () => {
    expect(Object.keys(reference).length).toBeGreaterThanOrEqual(16);
  });

  it("is word for word the glossary of CONTENT.md, in both directions", () => {
    expect(GLOSSARY).toEqual(reference);
  });

  it("gives the definition of a term and refuses a term it does not have", () => {
    expect(definitionOf("IP")).toBe("Innings pitched. 6.1 means six innings and one out.");
    expect(() => definitionOf("xwOBA")).toThrow();
  });

  it("keeps each definition to one or two sentences", () => {
    for (const [term, definition] of Object.entries(GLOSSARY)) {
      const sentences = definition.split(/(?<=[.!?])\s+/).length;
      expect(sentences, term).toBeLessThanOrEqual(3);
    }
  });
});
