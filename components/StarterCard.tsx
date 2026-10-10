import type { PitchLocation, Starter, StarterLine } from "@/lib/types";
import StatTile from "@/components/StatTile";
import TeamBadge from "@/components/TeamBadge";
import ZoneDiagram from "@/components/ZoneDiagram";
import { getTeamColor } from "@/lib/teamColors";

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

  const bio = starter.bio
    ? [
        `Age ${starter.bio.age}`,
        starter.bio.height,
        `${starter.bio.weight} lb`,
        `B/T ${starter.bio.bats}/${starter.bio.throws}`,
        starter.bio.mlb_service,
        starter.bio.accolades.join(", "),
      ].filter(Boolean)
    : ["Bio not available"];

  const throwsHand = normalizeThrows(starter.throws);
  const teamColor = getTeamColor(starter.team);

  return (
    <article
      className="rounded-xl border border-neutral-200 border-t-[3px] bg-white p-4"
      style={{ borderTopColor: teamColor.bg }}
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="font-mono text-[10px] font-semibold uppercase tracking-widest text-neutral-400">
            {starter.team} &middot; {sideLabel[side]}
          </p>
          <h3 className="mt-2 text-xl font-bold leading-tight text-neutral-900">{starter.name}</h3>
        </div>
        <TeamBadge abbreviation={starter.team} size={42} />
      </div>
      <p className="mt-2 text-[11px] leading-5 text-neutral-500">{bio.join(" · ")}</p>
      <p className="mt-1 text-[12px] font-semibold text-neutral-700">
        {throwsHand}HP &middot; {starter.pitching_profile.style_label}
      </p>
      <dl className="mt-4 grid grid-cols-3 gap-2">
        <StatTile label="ERA" title="Earned Run Average. Lower is better." value={starter.season_summary.era} />
        <StatTile label="WHIP" title="Walks plus hits per inning pitched. Lower is better." value={starter.season_summary.whip} />
        <StatTile label="K" title="Strikeouts." value={starter.season_summary.strikeouts} />
      </dl>
      <div className="mt-4 flex items-center gap-3.5">
        <ZoneDiagram locations={locations} width={64} height={76} />
        <p className="text-[13px] leading-5 text-neutral-600">
          {starter.recent_form?.last_three_starts_summary ?? "Recent form not available"}
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
  const teamColor = getTeamColor(starter.team);

  return (
    <article
      className="rounded-xl border border-neutral-200 border-t-[3px] bg-white p-4"
      style={{ borderTopColor: teamColor.bg }}
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <span className="font-mono text-[10px] font-semibold uppercase tracking-widest text-neutral-400">
              {starter.team} &middot; {sideLabel[side]}
            </span>
            <span className="rounded-md bg-neutral-100 px-1.5 py-1 font-mono text-[9px] font-semibold uppercase tracking-wide text-neutral-500">
              Game Score {starterLine.game_score}
            </span>
          </div>
          <h3 className="mt-2 text-xl font-bold leading-tight text-neutral-900">{starter.name}</h3>
        </div>
        <span
          className={`flex shrink-0 items-center justify-center rounded-full font-mono text-base font-bold ring-2 ${gradeClass(starterLine.pitchcraft_grade)}`}
          style={{ width: 44, height: 44 }}
        >
          {starterLine.pitchcraft_grade}
        </span>
      </div>
      <dl className="mt-4 grid grid-cols-4 gap-1.5">
        <StatTile label="IP" title="Innings pitched." value={starterLine.innings_pitched} align="center" />
        <StatTile label="ER" title="Earned runs allowed." value={starterLine.earned_runs} align="center" />
        <StatTile label="K" title="Strikeouts." value={starterLine.strikeouts} align="center" />
        <StatTile label="BB" title="Walks allowed." value={starterLine.walks} align="center" />
      </dl>
      <p className="mt-3.5 text-[13px] leading-6 text-neutral-600">{starterLine.grade_explanation}</p>
    </article>
  );
}

function normalizeThrows(raw: string): "L" | "R" {
  return raw?.toUpperCase().startsWith("L") ? "L" : "R";
}

function gradeClass(grade: string) {
  if (grade.startsWith("A")) return "bg-green-100 text-green-800 ring-green-200";
  if (grade.startsWith("B")) return "bg-blue-100 text-blue-800 ring-blue-200";
  if (grade.startsWith("C")) return "bg-amber-100 text-amber-800 ring-amber-200";
  return "bg-red-100 text-red-800 ring-red-200";
}
