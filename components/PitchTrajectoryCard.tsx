import TeamBadge from "@/components/TeamBadge";
import Tooltip, { STAT_TOOLTIPS } from "@/components/Tooltip";
import { getPitchColor } from "@/components/ZoneDiagram";
import { getTeamColor } from "@/lib/teamColors";
import type { PitchFamily } from "@/lib/types";

interface PitchTrajectoryCardProps {
  pitchName: string;
  family: PitchFamily | null;
  velocity: number | string;
  usagePct: number | null;
  hBreak: number;
  vBreak: number;
  throwsHand: "L" | "R" | null;
  team: string | null;
  description: string;
}

export default function PitchTrajectoryCard({
  pitchName,
  family,
  velocity,
  usagePct,
  hBreak,
  vBreak,
  throwsHand,
  team,
  description,
}: PitchTrajectoryCardProps) {
  const velo = typeof velocity === "number" ? velocity : Number.parseFloat(String(velocity));
  // An unavailable velocity has no meter: an empty bar beside "N/A" would read as a measured zero.
  const velocityPct = Number.isFinite(velo) ? clamp(((velo - 65) / 35) * 100, 0, 100) : null;
  const breakMagnitude = Math.sqrt(hBreak * hBreak + vBreak * vBreak);
  const breakPct = clamp((breakMagnitude / 20) * 100, 0, 100);
  const xOffset = clamp(hBreak * 3.4, -46, 46);
  const endX = 75 + xOffset;
  const endY = clamp(140 - vBreak * 2.3, 74, 170);
  const controlX = 75 + xOffset * 0.45;
  const controlY = 82;
  const stroke = getPitchColor(pitchName);
  const teamColor = getTeamColor(team);

  return (
    <aside className="rounded-lg border border-neutral-200 bg-white p-4 shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <h4 className="text-base font-bold text-neutral-900">{pitchName}</h4>
          {family ? (
            <span
              data-testid="pitch-family"
              className="rounded-md px-1.5 py-1 font-mono text-[9px] font-semibold uppercase tracking-wide"
              style={{ background: teamColor.bg, color: teamColor.ink }}
            >
              {family}
            </span>
          ) : null}
        </div>
        <TeamBadge abbreviation={team} size={20} fontSize={7.5} />
      </div>
      <p className="mt-1 font-mono text-[10.5px] text-neutral-400">
        {throwsHand ? `${throwsHand}HP shape` : "Pitch shape"} &middot; {formatVelocity(velocity)} &middot;{" "}
        {usagePct === null ? "usage not available" : `${usagePct}% usage`}
      </p>

      <svg
        role="img"
        aria-label={`${pitchName} movement trajectory`}
        viewBox="0 0 150 190"
        width="100%"
        height="190"
        className="mt-3 rounded-md bg-neutral-50"
      >
        <rect x="25" y="20" width="100" height="135" fill="#ffffff" stroke="#d4d4d4" strokeWidth="2" />
        {[1, 2].map((line) => (
          <g key={line} stroke="#e5e5e5" strokeWidth="1">
            <line x1={25 + line * (100 / 3)} y1="20" x2={25 + line * (100 / 3)} y2="155" />
            <line x1="25" y1={20 + line * (135 / 3)} x2="125" y2={20 + line * (135 / 3)} />
          </g>
        ))}
        <path
          d={`M 75 24 Q ${controlX} ${controlY} ${endX} ${endY}`}
          fill="none"
          stroke={stroke}
          strokeWidth="5"
          strokeLinecap="round"
        />
        <path
          d={`M ${endX - 7} ${endY - 5} L ${endX} ${endY} L ${endX - 2} ${endY - 9}`}
          fill="none"
          stroke={stroke}
          strokeWidth="3"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        <circle cx={endX} cy={endY} r="7" fill={stroke} />
        <circle cx="75" cy="24" r="4" fill="#a3a3a3" />
      </svg>

      <p className="mt-3 text-sm leading-6 text-neutral-700">{description}</p>

      <div className="mt-4 space-y-3">
        {velocityPct === null ? null : (
          <Meter label="Velocity" value={formatVelocity(velocity)} percent={velocityPct} color={stroke} />
        )}
        <Meter label="Break" value={`${breakMagnitude.toFixed(1)} in`} percent={breakPct} color={stroke} />
      </div>
    </aside>
  );
}

function Meter({ label, value, percent, color }: { label: string; value: string; percent: number; color: string }) {
  return (
    <div>
      <div className="flex items-center justify-between font-mono text-[9px] font-semibold uppercase tracking-wide text-neutral-400">
        {label === "Break" ? <Tooltip text={STAT_TOOLTIPS.Break}>{label}</Tooltip> : <span>{label}</span>}
        <span className="text-neutral-700" style={{ fontVariantNumeric: "tabular-nums" }}>{value}</span>
      </div>
      <div className="mt-1 h-[5px] rounded-full bg-neutral-200">
        <div className="h-[5px] rounded-full" style={{ width: `${percent}%`, backgroundColor: color }} />
      </div>
    </div>
  );
}

function formatVelocity(velocity: number | string) {
  if (typeof velocity === "number" && Number.isFinite(velocity)) return `${velocity} mph`;
  if (typeof velocity === "string" && velocity.trim()) return velocity;
  return "N/A";
}

function clamp(value: number, min: number, max: number) {
  return Math.min(Math.max(value, min), max);
}
