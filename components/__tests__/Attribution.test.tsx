import { readFileSync } from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";
import { render } from "@testing-library/react";
import Disclaimer from "@/components/Disclaimer";
import PitchCraftApp from "@/components/PitchCraftApp";
import type { Metadata, PitchCraftData } from "@/lib/types";
import { makeMatchup } from "./fixtures";

// P1.9 (D16, docs/plans/P1.md section 10): the foot of the page says where the data comes from and that PitchCraft is
// free, in both modes, and draws no ad, no tracker of its own and no link out of MLB / Baseball Savant. The texts are the
// owner's; the live file's four notes and the demo file's notes are written by the generator (tests/test_attribution.py
// checks the files), so these tests give the page those notes and check what it draws.

const ATTRIBUTION = "Data from the MLB Stats API and Baseball Savant (Statcast), made public by MLB Advanced Media. PitchCraft is an independent fan project and is not affiliated with MLB.";
const NON_COMMERCIAL = "PitchCraft is free and non-commercial: no ads, no sponsorships and no paid features.";
const CACHING = "Requests to the data sources are cached and the data is not downloaded in bulk.";
const INFORMATION_ONLY = "For information only: no predictions and no betting advice.";

const DEMO_ATTRIBUTION =
  "Demo data. Live reports use data from the MLB Stats API and Baseball Savant (Statcast). Not affiliated with MLB.";
const SOURCE_NAMES = ["MLB Stats API", "Baseball Savant"];

const LIVE_NOTES = [ATTRIBUTION, NON_COMMERCIAL, CACHING, INFORMATION_ONLY];
const DEMO_NOTES = [
  "PitchCraft is a capstone demo and not a betting or gambling tool.",
  NON_COMMERCIAL,
  DEMO_ATTRIBUTION,
  "The analysis explains matchup fit and what to watch, not guaranteed outcomes.",
  "Cached demo data may be used to ensure stable public evaluation.",
];

function metadata(mode: string): Metadata {
  return {
    project_name: "PitchCraft",
    version: "0.9.0",
    data_mode: mode,
    generated_at: "2026-10-23T15:00:03+00:00",
    data_fetched_at: mode === "fetched_snapshot" ? "2026-10-23T15:00:01+00:00" : null,
    last_updated_label: "",
    data_sources: [],
  };
}

function file(mode: string, disclaimers: string[]): PitchCraftData {
  return {
    metadata: metadata(mode),
    featured_matchup_id: "matchup_test",
    matchups: [makeMatchup({})],
    archive: [],
    agent_workflow: { description: "How the agents work.", steps: [] },
    disclaimers,
  };
}

// The notes of the file the site serves today, read from disk: not typed here, so a file without the attribution fails.
const SERVED = JSON.parse(readFileSync(path.join(process.cwd(), "public", "data", "pitchcraft-demo.json"), "utf-8")) as PitchCraftData;

describe("the notes at the foot of the page", () => {
  it("draw every note of a live file, in order", () => {
    const { container } = render(<Disclaimer disclaimers={LIVE_NOTES} />);

    expect(Array.from(container.querySelectorAll("li")).map((item) => item.textContent)).toEqual(LIVE_NOTES);
  });

  it("live page: the attribution, the non-commercial note and the caching note are on the page", () => {
    const { container } = render(<PitchCraftApp data={file("fetched_snapshot", LIVE_NOTES)} />);
    const footer = container.querySelector("footer")?.textContent ?? "";

    expect(footer).toContain(ATTRIBUTION);
    expect(footer).toContain(NON_COMMERCIAL);
    expect(footer).toContain(CACHING);
    expect(footer).toContain(INFORMATION_ONLY);
  });

  it.each(["demo_cached", "demo_fallback"])(
    "%s page: the non-commercial note is on the page and the caching note is not",
    (mode) => {
      const { container } = render(<PitchCraftApp data={file(mode, DEMO_NOTES)} />);
      const footer = container.querySelector("footer")?.textContent ?? "";

      expect(footer).toContain(NON_COMMERCIAL);
      expect(footer).not.toContain(CACHING);
    },
  );

  it.each(["demo_cached", "demo_fallback"])(
    "%s page: the demo notes name the MLB Stats API and Baseball Savant (QA1-03)",
    (mode) => {
      const { container } = render(<PitchCraftApp data={file(mode, DEMO_NOTES)} />);
      const footer = container.querySelector("footer")?.textContent ?? "";

      expect(footer).toContain(DEMO_ATTRIBUTION);
      for (const name of SOURCE_NAMES) expect(footer).toContain(name);
    },
  );

  it("live page: the notes name the MLB Stats API and Baseball Savant and carry no demo sentence", () => {
    const { container } = render(<PitchCraftApp data={file("fetched_snapshot", LIVE_NOTES)} />);
    const footer = container.querySelector("footer")?.textContent ?? "";

    for (const name of SOURCE_NAMES) expect(footer).toContain(name);
    expect(footer).not.toContain(DEMO_ATTRIBUTION);
  });

  it("the footer of the file the site serves names the MLB Stats API and Baseball Savant", () => {
    const { container } = render(<PitchCraftApp data={SERVED} />);
    const footer = container.querySelector("footer")?.textContent ?? "";

    expect(SERVED.disclaimers.length).toBeGreaterThan(0);
    expect(footer).toContain(NON_COMMERCIAL);
    for (const name of SOURCE_NAMES) expect(footer).toContain(name);
  });

  it.each([
    ["fetched_snapshot", LIVE_NOTES],
    ["demo_cached", DEMO_NOTES],
  ])("%s page draws no link, image, script, frame or form of its own", (mode, notes) => {
    const { container } = render(<PitchCraftApp data={file(mode, notes)} />);

    expect(container.querySelectorAll("a, img, script, iframe, form, embed, object, video, audio")).toHaveLength(0);
  });
});
