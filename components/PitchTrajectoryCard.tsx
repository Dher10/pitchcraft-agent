import type { PitchFamily } from "@/lib/types";

interface PitchTrajectoryCardProps {
  pitchName: string;
  family: PitchFamily;
  velocity: number | string;
  usagePct: number;
  hBreak: number;
  vBreak: number;
  throwsHand: "L" | "R";
  description: string;
}

const familyClasses: Record<PitchFamily, string> = {
  Fastball: "bg-red-50 text-red-700 ring-red-200",
  Breaking: "bg-blue-50 text-blue-700 ring-blue-200",
  Offspeed: "bg-amber-50 text-amber-700 ring-amber-200",
};

const familyStroke: Record<PitchFamily, string> = {
  Fastball: "#D85A30",
  Breaking: "#378ADD",
  Offspeed: "#A855F7",
};

export default function PitchTrajectoryCard({
  pitchName,
  family,
  velocity,
  usagePct,
  hBreak,
  vBreak,
  throwsHand,
  description,
}: PitchTrajectoryCardProps) {
  const velo = typeof velocity === "number" ? velocity : Number.parseFloat(String(velocity));
  const velocityPct = Number.isFinite(velo) ? clamp(((velo - 65) / 35) * 100, 0, 100) : 0;
  const breakMagnitude = Math.sqrt(hBreak * hBreak + vBreak * vBreak);
  const breakPct = clamp((breakMagnitude / 20) * 100, 0, 100);
  const xOffset = clamp(hBreak * 3.4, -46, 46);
  const endX = 75 + xOffset;
  const endY = clamp(140 - vBreak * 2.3, 74, 170);
  const controlX = 75 + xOffset * 0.45;
  const controlY = 82;
  const stroke = familyStroke[family];

  return (
    <aside className="rounded-lg border border-neutral-200 bg-white p-4 shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <div className="flex items-center gap-2">
            <h4 className="text-base font-bold text-neutral-900">{pitchName}</h4>
            <span className={`rounded-full px-2 py-0.5 text-[11px] font-bold ring-1 ${familyClasses[family]}`}>
              {family}
            </span>
          </div>
          <p className="mt-1 text-xs font-semibold text-neutral-500">{throwsHand}HP shape</p>
        </div>
        <div className="text-right text-xs font-semibold text-neutral-500" style={{ fontVariantNumeric: "tabular-nums" }}>
          <p>{formatVelocity(velocity)}</p>
          <p>{usagePct}% usage</p>
        </div>
      </div>

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
        <Meter label="Velocity" value={formatVelocity(velocity)} percent={velocityPct} color={stroke} />
        <Meter label="Break" value={`${breakMagnitude.toFixed(1)} in`} percent={breakPct} color={stroke} />
      </div>
    </aside>
  );
}

function Meter({ label, value, percent, color }: { label: string; value: string; percent: number; color: string }) {
  return (
    <div>
      <div className="flex items-center justify-between text-xs font-semibold text-neutral-500">
        <span>{label}</span>
        <span style={{ fontVariantNumeric: "tabular-nums" }}>{value}</span>
      </div>
      <div className="mt-1 h-2.5 rounded-full bg-neutral-200">
        <div className="h-2.5 rounded-full" style={{ width: `${percent}%`, backgroundColor: color }} />
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
