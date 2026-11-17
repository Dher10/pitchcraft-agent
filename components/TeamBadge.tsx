import { getTeamColor } from "@/lib/teamColors";

interface TeamBadgeProps {
  abbreviation: string | null;
  /** 24 (tables), 34 (rows), 48 (boards and page heads). */
  size?: number;
  fontSize?: number;
  /** On the board the badge gets a thin ring so navy clubs stay visible. */
  onBoard?: boolean;
}

/** The smallest readable text in a badge: 12 px, the floor of the design system. */
function defaultFontSize(size: number): number {
  if (size <= 24) return 12;
  if (size <= 34) return 13;
  return Math.max(12, Math.round(size * 0.36));
}

/**
 * A circle in the team's approximate color with its abbreviation in the display face. The badge is decoration: the team
 * name is always in text next to it. Colors come from `lib/teamColors.ts` (approximate and unlicensed).
 */
export default function TeamBadge({ abbreviation, size = 42, fontSize, onBoard = false }: TeamBadgeProps) {
  const { bg, ink } = getTeamColor(abbreviation);
  return (
    <span
      className={`flex shrink-0 items-center justify-center rounded-full font-display font-extrabold tracking-[0.03em] ${
        onBoard ? "ring-1 ring-on-board-2 ring-offset-2 ring-offset-board" : ""
      }`}
      style={{
        width: size,
        height: size,
        background: bg,
        color: ink,
        fontSize: fontSize ?? defaultFontSize(size),
        lineHeight: 1,
      }}
      aria-hidden="true"
    >
      {abbreviation ?? ""}
    </span>
  );
}
