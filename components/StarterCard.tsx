import type { PitchLocation, Starter, StarterLine } from "@/lib/types";
import ZoneDiagram from "@/components/ZoneDiagram";

interface StarterCardProps {
  starter: Starter;
  side: "away" | "home";
  mode: "pregame" | "postgame";
  starterLine?: StarterLine;
  locations?: PitchLocation[];
}

const sideLabel = {
  away: "AWAY",
  home: "HOME",
};

export default function StarterCard({
  starter,
  side,
  mode,
  starterLine,
  locations = [],
}: StarterCardProps) {
  if (mode === "postgame" && starterLine) {
    return <PostgameStarter starter={starter} side={side} starterLine={starterLine} />;
  }

  const bio = [
    `Age ${starter.bio.age}`,
    starter.bio.height,
    `${starter.bio.weight} lb`,
    `B/T ${starter.bio.bats}/${starter.bio.throws}`,
    starter.bio.mlb_service,
    starter.bio.accolades.join(", "),
  ].filter(Boolean);

  const throwsHand = normalizeThrows(starter.throws);

  return (
    <article className="rounded-xl border border-neutral-200 bg-white p-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-widest text-neutral-500">
            {starter.team} - {sideLabel[side]}
          </p>
          <h3 className="mt-2 text-2xl font-bold text-neutral-900">{starter.name}</h3>
        </div>
        <PitcherSilhouette throwsHand={throwsHand} />
      </div>
      <p className="mt-2 text-xs leading-5 text-neutral-500">{bio.join(" - ")}</p>
      <p className="mt-3 text-sm font-semibold text-neutral-800">
        {throwsHand}HP - {starter.pitching_profile.style_label}
      </p>
      <dl className="mt-4 grid grid-cols-3 gap-2 text-sm" style={{ fontVariantNumeric: "tabular-nums" }}>
        <Stat label="ERA" title="Earned Run Average. Lower is better." value={starter.season_summary.era} />
        <Stat label="WHIP" title="Walks plus hits per inning pitched. Lower is better." value={starter.season_summary.whip} />
        <Stat label="K" title="Strikeouts." value={starter.season_summary.strikeouts} />
      </dl>
      <div className="my-4 border-t border-neutral-200" />
      <div className="flex items-center justify-between gap-4">
        <ZoneDiagram locations={locations} />
        <p className="text-sm leading-6 text-neutral-600">
          {starter.recent_form.last_three_starts_summary}
        </p>
      </div>
    </article>
  );
}

function PostgameStarter({
  starter,
  side,
  starterLine,
}: {
  starter: Starter;
  side: "away" | "home";
  starterLine: StarterLine;
}) {
  return (
    <article className="rounded-xl border border-neutral-200 bg-white p-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-widest text-neutral-500">
            {starter.team} - {sideLabel[side]}
          </p>
          <h3 className="mt-2 text-2xl font-bold text-neutral-900">{starter.name}</h3>
        </div>
        <div className="flex flex-wrap items-center justify-end gap-2">
          <span className="rounded-full bg-neutral-100 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-neutral-700">
            <span
              title="Game Score (Bill James): a 0-100 rating of a single start. ~50 is average, 65+ is very good."
              className="cursor-help"
            >
              Game Score
            </span>{" "}
            {starterLine.game_score}
          </span>
          <span className={`rounded-full px-3 py-1.5 text-2xl font-bold ${gradeClass(starterLine.pitchcraft_grade)}`}>
            {starterLine.pitchcraft_grade}
          </span>
        </div>
      </div>
      <dl className="mt-4 grid grid-cols-4 gap-2 text-sm" style={{ fontVariantNumeric: "tabular-nums" }}>
        <Stat label="IP" title="Innings pitched." value={starterLine.innings_pitched} />
        <Stat label="ER" title="Earned runs allowed." value={starterLine.earned_runs} />
        <Stat label="K" title="Strikeouts." value={starterLine.strikeouts} />
        <Stat label="BB" title="Walks allowed." value={starterLine.walks} />
      </dl>
      <p className="mt-4 text-sm leading-6 text-neutral-600">{starterLine.grade_explanation}</p>
    </article>
  );
}

function PitcherSilhouette({ throwsHand }: { throwsHand: "L" | "R" }) {
  return (
    <div className="flex shrink-0 items-center gap-2" aria-hidden="true">
      <svg
        viewBox="0 0 100 100"
        width="56"
        height="56"
        className="text-neutral-500 opacity-20"
        style={{ transform: throwsHand === "L" ? "scaleX(-1)" : undefined }}
      >
        <circle cx="42" cy="16" r="8" fill="currentColor" />
        <path
          d="M40 25 C33 28 29 36 31 45 L35 58 L20 75 C17 78 18 84 22 86 C25 88 29 87 32 84 L49 64 C51 61 51 58 49 54 L45 44 L55 49 L71 70 C74 74 80 75 83 72 C86 69 86 64 83 60 L64 36 C61 32 57 30 52 29 L57 18 L72 12 C76 10 78 6 76 3 C74 0 70 0 66 2 L49 10 C46 12 44 15 43 18 Z"
          fill="currentColor"
        />
        <path
          d="M34 37 L16 29 C12 27 8 29 7 33 C6 36 8 40 12 42 L31 51 Z"
          fill="currentColor"
        />
      </svg>
    </div>
  );
}

function normalizeThrows(raw: string): "L" | "R" {
  return raw?.toUpperCase().startsWith("L") ? "L" : "R";
}

function Stat({ label, title, value }: { label: string; title: string; value: string | number }) {
  return (
    <div className="rounded-lg bg-neutral-50 p-2">
      <dt className="text-[11px] font-semibold uppercase tracking-wide text-neutral-500">
        <span title={title} className="cursor-help border-b border-dotted border-neutral-400">
          {label}
        </span>
      </dt>
      <dd className="mt-1 font-bold text-neutral-900">{value}</dd>
    </div>
  );
}

function gradeClass(grade: string) {
  if (grade.startsWith("A")) return "bg-green-100 text-green-800";
  if (grade.startsWith("B")) return "bg-blue-100 text-blue-800";
  if (grade.startsWith("C")) return "bg-amber-100 text-amber-800";
  return "bg-red-100 text-red-800";
}
