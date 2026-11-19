import { readFileSync } from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";

// Release 2.2.0 item 2: browsers request /favicon.ico. Next.js serves app/favicon.ico at that URL, so the file must exist
// and be a real icon (ICO container, 16 and 32 px images), made from the mark of app/icon.svg.

const FILE = path.join(process.cwd(), "app/favicon.ico");
const PNG = Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]);

function read(): Buffer {
  try {
    return readFileSync(FILE);
  } catch {
    return Buffer.alloc(0);
  }
}

describe("app/favicon.ico", () => {
  it("exists and is an ICO file with images of 16 and 32 px", () => {
    const ico = read();
    expect(ico.length).toBeGreaterThan(22);
    expect(ico.readUInt16LE(0)).toBe(0); // reserved
    expect(ico.readUInt16LE(2)).toBe(1); // type: icon
    const count = ico.readUInt16LE(4);
    const sizes = Array.from({ length: count }, (_, i) => ico[6 + 16 * i] || 256).sort((a, b) => a - b);
    expect(sizes).toEqual([16, 32]);
  });

  it("holds PNG images that match their directory entries and stay inside the file", () => {
    const ico = read();
    const count = ico.readUInt16LE(4);
    expect(count).toBe(2);
    for (let i = 0; i < count; i += 1) {
      const entry = 6 + 16 * i;
      const size = ico[entry];
      const bytes = ico.readUInt32LE(entry + 8);
      const offset = ico.readUInt32LE(entry + 12);
      expect(offset + bytes).toBeLessThanOrEqual(ico.length);
      const image = ico.subarray(offset, offset + bytes);
      expect(image.subarray(0, 8).equals(PNG)).toBe(true);
      expect(image.readUInt32BE(16)).toBe(size); // PNG width
      expect(image.readUInt32BE(20)).toBe(size); // PNG height
    }
  });

  it("keeps app/icon.svg beside it, the source of the mark", () => {
    expect(readFileSync(path.join(process.cwd(), "app/icon.svg"), "utf8")).toContain("<svg");
  });
});
