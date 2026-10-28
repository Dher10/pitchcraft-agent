import { describe, expect, it } from "vitest";
import { render } from "@testing-library/react";
import ArchiveTable from "@/components/ArchiveTable";
import type { ArchiveItem } from "@/lib/types";

// D43: historical live reports may be carried forward; an empty archive has no headers.

const row: ArchiveItem = {
  id: "matchup_002",
  date: "2026-06-27",
  title: "Dodgers vs Giants",
  status: "final",
  featured: false,
  starter_summary: "A vs B",
  result_label: "Final",
  grade_label: "Starter Duel: B, B",
};

describe("the archive table", () => {
  it("says there are no past reports when the archive is empty, and draws no table", () => {
    const { container } = render(<ArchiveTable archive={[]} />);

    expect(container.textContent).toContain("No past reports yet");
    expect(container.querySelector("table")).toBeNull();
  });

  it("control: an archive with rows is drawn as before and has no empty message", () => {
    const { container } = render(<ArchiveTable archive={[row]} />);

    expect(container.querySelectorAll("tbody tr")).toHaveLength(1);
    expect(container.textContent).not.toContain("No past reports yet");
  });

  it.each(["upcoming", "live", "final", "demo", null] as const)(
    "does not present publication-time status %s as the archived game's current state",
    (status) => {
      const { container } = render(<ArchiveTable archive={[{ ...row, status }]} />);
      const headers = Array.from(container.querySelectorAll("th")).map((cell) => cell.textContent);
      expect(headers).toEqual(["Date", "Matchup", "Starters", "Result", "Grade"]);
      expect(container.querySelectorAll("tbody td")).toHaveLength(5);
    },
  );

  it("does not carry the featured badge into an earlier report", () => {
    const { container } = render(<ArchiveTable archive={[{ ...row, featured: true }]} />);
    expect(container.textContent).not.toMatch(/featured/i);
    expect(container.textContent).toContain("Dodgers vs Giants");
  });

  it("constrains long archive cells to the desktop card while allowing phone scrolling", () => {
    const { container } = render(<ArchiveTable archive={[{
      ...row,
      title: "Arizona Diamondbacks vs San Francisco Giants",
      starter_summary: "A very long starter name vs Another very long starter name",
    }]} />);
    const table = container.querySelector("table")!;
    // jsdom checks responsive constraints, not geometry; browser availability is recorded in STATUS.
    expect(table.classList.contains("sm:min-w-0")).toBe(true);
    expect(table.classList.contains("sm:table-fixed")).toBe(true);
    expect(table.classList.contains("[&_td]:break-words")).toBe(true);
    expect(table.parentElement!.classList.contains("overflow-x-auto")).toBe(true);
    expect(table.textContent).toContain("Arizona Diamondbacks");
  });
});
