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

  return (
    <article className="rounded-xl border border-neutral-200 bg-white p-4">
      <p className="text-xs font-semibold uppercase tracking-widest text-neutral-500">
        {starter.team} - {sideLabel[side]}
      </p>
      <h3 className="mt-2 text-2xl font-bold text-neutral-900">{starter.name}</h3>
      <p className="mt-2 text-xs leading-5 text-neutral-500">{bio.join(" - ")}</p>
      <p className="mt-3 text-sm font-semibold text-neutral-800">
        {starter.throws} - {starter.pitching_profile.style_label}
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
