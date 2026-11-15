import { readFileSync } from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";
import { CLUBS, clubNickname } from "@/lib/teams";
import { parseArchiveIndex } from "@/lib/archiveIndex";
import { getTeamColor } from "@/lib/teamColors";

// The nicknames of the 30 clubs are a closed table of static labels (data contract 3.4): they assert nothing about data.

const THIRTY = [
  "BAL", "BOS", "NYY", "TB", "TOR", "CWS", "CLE", "DET", "KC", "MIN", "ATH", "HOU", "LAA", "SEA", "TEX",
  "ATL", "MIA", "NYM", "PHI", "WSH", "CHC", "CIN", "MIL", "PIT", "STL", "ARI", "COL", "LAD", "SD", "SF",
];

describe("the club table", () => {
  it("has exactly the 30 clubs, each with a nickname and a league and division", () => {
    expect(Object.keys(CLUBS).sort()).toEqual([...THIRTY].sort());
    const leagues = new Set(Object.values(CLUBS).map((club) => `${club.league} ${club.division}`));
    expect(leagues.size).toBe(6);
    for (const club of Object.values(CLUBS)) expect(club.nickname.trim().length).toBeGreaterThan(0);
  });

  it("has a team color for every club", () => {
    for (const abbreviation of THIRTY) {
      expect(getTeamColor(abbreviation).bg, abbreviation).not.toBe(getTeamColor(null).bg);
    }
  });

  it("names the clubs the design names", () => {
    expect(clubNickname("MIL")).toBe("Brewers");
    expect(clubNickname("TB")).toBe("Rays");
    expect(clubNickname("TOR")).toBe("Blue Jays");
    expect(clubNickname("CWS")).toBe("White Sox");
    expect(clubNickname("ARI")).toBe("D-backs");
    expect(clubNickname("ATH")).toBe("Athletics");
  });

  it("returns null for an unknown or missing abbreviation, never a placeholder", () => {
    expect(clubNickname("XXX")).toBeNull();
    expect(clubNickname(null)).toBeNull();
    expect(clubNickname("")).toBeNull();
  });

  it("covers every club of the published archive", () => {
    const index = parseArchiveIndex(
      JSON.parse(readFileSync(path.join(process.cwd(), "public/data/archive/index-2026.json"), "utf8")),
    );
    const seen = new Set(index.games.flatMap((game) => [game.away.abbreviation, game.home.abbreviation]));
    expect(seen.size).toBeGreaterThan(10);
    for (const abbreviation of seen) expect(clubNickname(abbreviation), String(abbreviation)).not.toBeNull();
  });
});
