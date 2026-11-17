import { SITE_COPY } from "@/lib/copy/site";
import { formatDay, formatModeLine } from "@/lib/format";

type ModeLineProps = { onBoard?: boolean } & (
  | { dataMode: string; fetchedAt: string | null | undefined; archive?: undefined }
  | { archive: { season: number; through: string }; dataMode?: undefined; fetchedAt?: undefined }
);

const LOOK = {
  live: { light: "bg-ok-tint text-ok", board: "bg-board-2 text-on-board", dot: "rounded-full bg-ok", boardDot: "rounded-full bg-signal" },
  demo: { light: "bg-warn-tint text-warn", board: "bg-warn-tint text-warn", dot: "rounded-[1px] bg-warn", boardDot: "rounded-[1px] bg-warn" },
  archive: { light: "bg-surface-sunken text-ink-2", board: "bg-board-2 text-on-board", dot: "rounded-full bg-ink-3", boardDot: "rounded-full bg-signal" },
} as const;

/**
 * Rule 6: the page says what kind of data it shows. Live only for a fetched snapshot, demo for anything else, and the
 * archive line for the off season (the index's last game date). The dot's shape differs by kind, so color is never
 * alone. Dates are written for people; ISO stays in the `datetime` attribute.
 */
export default function ModeLine(props: ModeLineProps) {
  const kind = props.archive ? "archive" : props.dataMode === "fetched_snapshot" ? "live" : "demo";
  const look = LOOK[kind];
  return (
    <p
      data-testid="mode-line"
      data-mode={kind}
      className={`m-0 inline-flex items-center gap-space-2 rounded-sm px-2.5 py-1.5 text-label ${props.onBoard ? look.board : look.light}`}
    >
      <span aria-hidden="true" className={`size-2 flex-none ${props.onBoard ? look.boardDot : look.dot}`} />
      {props.archive ? (
        <span>
          {SITE_COPY.archiveModeLinePrefix(props.archive.season)}{" "}
          <time dateTime={props.archive.through}>{formatDay(props.archive.through)}</time>
        </span>
      ) : (
        formatModeLine(props.dataMode, props.fetchedAt)
      )}
    </p>
  );
}
