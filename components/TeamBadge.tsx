import { getTeamColor } from "@/lib/teamColors";

interface TeamBadgeProps {
  abbreviation: string;
  size?: number;
  fontSize?: number;
}

export default function TeamBadge({ abbreviation, size = 42, fontSize }: TeamBadgeProps) {
  const { bg, ink } = getTeamColor(abbreviation);
  return (
    <span
      className="flex shrink-0 items-center justify-center rounded-full font-mono font-bold"
      style={{
        width: size,
        height: size,
        background: bg,
        color: ink,
        fontSize: fontSize ?? Math.max(8, Math.round(size * 0.3)),
        boxShadow: "inset 0 0 0 1.5px rgba(0,0,0,.08)",
      }}
      aria-hidden="true"
    >
      {abbreviation}
    </span>
  );
}
