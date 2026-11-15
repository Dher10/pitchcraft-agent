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

describe("the indexed archive's opt-in Grade rule", () => {
  it("hides Grade and all grade cells when opted in and no row has a grade", () => {
    const { container } = render(<ArchiveTable
      archive={[
        { ...row, title: "Milwaukee Brewers vs Tampa Bay Rays", result_label: "MIL 4 - TB 0", grade_label: null },
        { ...row, id: "849805", title: "Milwaukee Brewers vs Tampa Bay Rays", result_label: "MIL 0 - TB 2", grade_label: null },
      ]}
      hideGradeWhenEmpty
    />);

    expect(Array.from(container.querySelectorAll("th"), (cell) => cell.textContent)).toEqual([
      "Date", "Matchup", "Starters", "Result",
    ]);
    expect(Array.from(container.querySelectorAll("tbody tr"), (item) => item.querySelectorAll("td").length)).toEqual([4, 4]);
    expect(container.textContent).not.toContain("Pending");
    expect(container.textContent).toContain("MIL 4 - TB 0");
    expect(container.textContent).toContain("MIL 0 - TB 2");
  });

  it("shows Grade for every row as soon as any opted-in row has a grade", () => {
    const { container } = render(<ArchiveTable
      archive={[
        { ...row, id: "849806", title: "Milwaukee Brewers vs Tampa Bay Rays", result_label: "MIL 4 - TB 0", grade_label: null },
        { ...row, id: "849805", title: "Milwaukee Brewers vs Tampa Bay Rays", result_label: "MIL 0 - TB 2", grade_label: "Starter Duel: A, B" },
        { ...row, id: "legacy", result_label: null, grade_label: null },
      ]}
      hideGradeWhenEmpty
    />);

    expect(Array.from(container.querySelectorAll("th"), (cell) => cell.textContent)).toEqual([
      "Date", "Matchup", "Starters", "Result", "Grade",
    ]);
    const rows = Array.from(container.querySelectorAll("tbody tr"));
    expect(rows.map((item) => item.querySelectorAll("td").length)).toEqual([5, 5, 5]);
    expect(rows.map((item) => item.querySelectorAll("td")[4].textContent)).toEqual([
      "Pending", "Starter Duel: A, B", "—",
    ]);
  });

  it("control: the default keeps the legacy Grade column when no row is graded", () => {
    const { container } = render(<ArchiveTable archive={[{ ...row, grade_label: null }]} />);
    expect(Array.from(container.querySelectorAll("th"), (cell) => cell.textContent)).toEqual([
      "Date", "Matchup", "Starters", "Result", "Grade",
    ]);
    expect(container.querySelectorAll("tbody td")).toHaveLength(5);
    expect(container.querySelectorAll("tbody td")[4].textContent).toBe("Pending");
  });

  it("control: explicitly false keeps the legacy Grade column", () => {
    const { container } = render(<ArchiveTable archive={[{ ...row, grade_label: null }]} hideGradeWhenEmpty={false} />);
    expect(container.querySelectorAll("th")[4].textContent).toBe("Grade");
    expect(container.querySelectorAll("tbody td")[4].textContent).toBe("Pending");
  });

  it("keeps the current phone scrolling and desktop wrapping when Grade is hidden", () => {
    const { container } = render(<ArchiveTable archive={[{
      ...row,
      title: "Arizona Diamondbacks vs San Francisco Giants",
      starter_summary: "A very long starter name vs Another very long starter name",
      result_label: "Arizona Diamondbacks 0 - San Francisco Giants 1",
      grade_label: null,
    }]} hideGradeWhenEmpty />);
    const table = container.querySelector("table")!;

    // jsdom proves the existing constraints remain, not the rendered geometry.
    expect(table.classList.contains("w-full")).toBe(true);
    expect(table.classList.contains("min-w-[600px]")).toBe(true);
    expect(table.classList.contains("sm:min-w-0")).toBe(true);
    expect(table.classList.contains("sm:table-fixed")).toBe(true);
    expect(table.classList.contains("[&_td]:break-words")).toBe(true);
    expect(table.parentElement!.classList.contains("overflow-x-auto")).toBe(true);
    expect(table.closest("section")!.classList.contains("rounded-xl")).toBe(true);
    expect(table.closest("section")!.classList.contains("bg-white")).toBe(true);
    expect(container.querySelectorAll("th")).toHaveLength(4);
    expect(table.textContent).toContain("Arizona Diamondbacks 0 - San Francisco Giants 1");
    expect(table.querySelectorAll("a")).toHaveLength(0);
  });

  it("control: an opted-in empty archive keeps the existing empty state without a table", () => {
    const { container } = render(<ArchiveTable archive={[]} hideGradeWhenEmpty />);
    expect(container.textContent).toContain("No past reports yet");
    expect(container.querySelector("table")).toBeNull();
  });
});
