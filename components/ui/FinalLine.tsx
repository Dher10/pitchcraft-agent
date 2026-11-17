import { SITE_COPY } from "@/lib/copy/site";
import { UNAVAILABLE } from "@/lib/format";

export interface FinalLineData {
  innings_pitched: string | null;
  hits: number | null;
  earned_runs: number | null;
  walks: number | null;
  strikeouts: number | null;
}

export type FinalLineField = keyof FinalLineData;

const ORDER: FinalLineField[] = ["innings_pitched", "hits", "earned_runs", "walks", "strikeouts"];

/**
 * A starter's line in one game, from the box score: a ruled strip of equal cells (docs/design/COMPONENTS.md, FinalLine).
 * No pitches cell: the 1.0.0 game files do not keep a pitch count. A real 0 shows 0; a field the box score does not give
 * shows the dash and says so to assistive tech; with no line at all the text says it is not available.
 */
export default function FinalLine({ line, featured = [] }: { line: FinalLineData | null; featured?: FinalLineField[] }) {
  if (line === null) {
    return <p className="m-0 text-body-sm text-ink-3">{SITE_COPY.finalLine.notAvailable}</p>;
  }
  return (
    <dl aria-label={SITE_COPY.finalLine.label} className="m-0 grid grid-cols-5 overflow-hidden rounded-sm border border-line bg-surface">
      {ORDER.map((field) => {
        const value = line[field];
        const { abbreviation, name } = SITE_COPY.finalLine.fields[field];
        const known = value !== null && value !== undefined;
        return (
          <div
            key={field}
            className={`border-l border-line py-space-2 text-center first:border-l-0 ${featured.includes(field) ? "bg-signal" : ""}`}
          >
            <dt className={`text-label ${featured.includes(field) ? "text-ink" : "text-ink-2"}`}>
              <span aria-hidden="true">{abbreviation}</span>
              <span className="sr-only">{name}</span>
            </dt>
            <dd className={`m-0 mt-1 font-display tabular-nums ${known ? "text-stat" : "text-stat font-medium text-ink-3"}`}>
              {known ? (
                value
              ) : (
                <>
                  <span aria-hidden="true">{UNAVAILABLE}</span>
                  <span className="sr-only">{SITE_COPY.figure.unavailable}</span>
                </>
              )}
            </dd>
          </div>
        );
      })}
    </dl>
  );
}
