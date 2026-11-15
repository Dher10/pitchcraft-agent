import Help from "@/components/ui/Help";
import Tooltip, { STAT_TOOLTIPS } from "@/components/Tooltip";
import { SITE_COPY } from "@/lib/copy/site";
import { UNAVAILABLE } from "@/lib/format";
import type { GlossaryTerm } from "@/lib/glossary";

interface StatTileProps {
  label: string;
  title?: string;
  /** A figure, or `null` when it is not available: the dash with "Not available", never 0 or blank. */
  value: string | number | null;
  align?: "left" | "center";
  /** Featured: the figure a notable reason points at. Limited: a small sample, with its sample stated in `note`. */
  state?: "featured" | "limited";
  note?: string;
  /** The glossary term to explain after the label (Help). Without it, the older tooltip texts apply. */
  help?: GlossaryTerm;
}

const TILE = { default: "bg-surface-sunken", featured: "bg-signal", limited: "bg-warn-tint" } as const;

/**
 * One figure with its label (docs/design/COMPONENTS.md, StatTile): the label on top in the text face, the value a
 * scoreboard numeral. A row of tiles carries one scope caption under it.
 */
export default function StatTile({ label, title, value, align = "center", state, note, help }: StatTileProps) {
  const known = value !== null && value !== undefined && value !== "";
  return (
    <div className={`min-w-0 rounded-sm px-space-3 py-space-2 ${TILE[state ?? "default"]} ${align === "center" ? "text-center" : ""}`}>
      <dt className={`flex items-center gap-1 text-label ${state === "featured" ? "text-ink" : "text-ink-2"} ${align === "center" ? "justify-center" : ""}`}>
        {help ? (
          <>
            {label}
            <Help term={help} />
          </>
        ) : STAT_TOOLTIPS[label] ? (
          <Tooltip text={STAT_TOOLTIPS[label]}>{label}</Tooltip>
        ) : (
          <span title={title} className="cursor-help">{label}</span>
        )}
      </dt>
      <dd className={`m-0 mt-1 font-display tabular-nums ${known ? "text-stat text-ink" : "text-stat font-medium text-ink-3"}`}>
        {known ? value : UNAVAILABLE}
      </dd>
      {!known ? <dd className="m-0 mt-0.5 text-caption text-ink-3">{SITE_COPY.figure.unavailable}</dd> : null}
      {known && note ? <dd className={`m-0 mt-0.5 text-caption ${state === "limited" ? "text-warn" : "text-ink-3"}`}>{note}</dd> : null}
    </div>
  );
}
