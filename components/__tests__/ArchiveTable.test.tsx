import { describe, expect, it } from "vitest";
import { render } from "@testing-library/react";
import ArchiveTable from "@/components/ArchiveTable";
import type { ArchiveItem } from "@/lib/types";

// P0.15-D2.4a (F4, contract 3.3): a live file has no archive rows (today's game is not a past report), so the table says
// so instead of drawing headers over nothing.

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
});
