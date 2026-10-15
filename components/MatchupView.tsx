"use client";

import { useState } from "react";
import CallCheck from "@/components/CallCheck";
import CriticReviewPanel from "@/components/CriticReviewPanel";
import DetailedAnalysis from "@/components/DetailedAnalysis";
import ScoutingReport from "@/components/ScoutingReport";
import StarterCard from "@/components/StarterCard";
import TeamBadge from "@/components/TeamBadge";
import { getPitchColor } from "@/components/ZoneDiagram";
import { formatStartTime } from "@/lib/format";
import { getTeamColor } from "@/lib/teamColors";
import { teamLabel } from "@/lib/teamLabel";
import type { Matchup, ReportSection } from "@/lib/types";

interface MatchupViewProps {
  matchup: Matchup;
}

export default function MatchupView({ matchup }: MatchupViewProps) {
  if (matchup.status === "final" && matchup.postgame) {
    return <PostgameMode matchup={matchup} />;
  }

  return <PregameMode matchup={matchup} />;
}

function PregameMode({ matchup }: { matchup: Matchup }) {
  const [showDetails, setShowDetails] = useState(false);
  const awaySection = findStarterSection(matchup.report.sections, "Pitcher A", matchup.starters.away_starter.name);
  const homeSection = findStarterSection(matchup.report.sections, "Pitcher B", matchup.starters.home_starter.name);
  const watchSection = matchup.report.sections.find((section) => section.title === "Three Things to Watch");

  return (
    <section className="space-y-4">
      <header className="rounded-xl border border-neutral-200 bg-white p-4">
        <p className="font-mono text-[11px] text-neutral-400">
          {matchup.game.venue ?? "Venue not available"} &middot; {formatStartTime(matchup.game)}
        </p>
        <h2 className="mt-2 text-2xl font-bold leading-tight tracking-tight text-neutral-900">{matchup.report.headline}</h2>
        {matchup.report.short_summary[0] ? (
          <div className="mt-3 inline-flex items-center gap-2 rounded-lg border border-blue-100 bg-blue-50 px-3 py-1.5">
            <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-blue-600" />
            <p className="text-[13px] font-medium leading-5 text-blue-800">{matchup.report.short_summary[0]}</p>
          </div>
        ) : null}
      </header>

      <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
        <StarterCard
          starter={matchup.starters.away_starter}
          teamName={matchup.teams.away.name}
          side="away"
          mode="pregame"
          locations={matchup.pitch_locations.away_starter.vs_rhh}
        />
        <StarterCard
          starter={matchup.starters.home_starter}
          teamName={matchup.teams.home.name}
          side="home"
          mode="pregame"
          locations={matchup.pitch_locations.home_starter.vs_rhh}
        />
      </div>

      <PitchLegend matchup={matchup} />

      <ScoutingReport
        awayStarter={matchup.starters.away_starter}
        homeStarter={matchup.starters.home_starter}
        awayOpponent={matchup.teams.home}
        homeOpponent={matchup.teams.away}
        awaySection={awaySection}
        homeSection={homeSection}
      />

      {watchSection?.bullets ? (
        <section className="px-2 py-3 text-center">
          <h2 className="text-lg font-bold text-neutral-900">What to watch</h2>
          <div className="mt-3 space-y-2 text-[13px] leading-6 text-neutral-600">
            {watchSection.bullets.map((bullet) => (
              <p key={bullet} className="mx-auto max-w-md">
                {bullet}
              </p>
            ))}
          </div>
        </section>
      ) : null}

      <button
        type="button"
        onClick={() => setShowDetails((current) => !current)}
        className={`flex w-full items-center justify-center gap-2 rounded-lg border px-4 py-3 text-sm font-semibold text-blue-700 transition ${
          showDetails ? "border-blue-200 bg-blue-50" : "border-neutral-200 bg-white hover:bg-blue-50"
        }`}
      >
        <span>{showDetails ? "Hide detailed analysis" : "See detailed analysis"}</span>
        <span className="font-mono text-[11px]">{showDetails ? "▲" : "▼"}</span>
      </button>

      {showDetails ? <DetailedAnalysis matchup={matchup} /> : null}
      <CriticReviewPanel criticReview={matchup.critic_review} />
    </section>
  );
}

function PostgameMode({ matchup }: { matchup: Matchup }) {
  const postgame = matchup.postgame;

  if (!postgame) return null;

  const winnerAbbr = teamAbbrForName(matchup, postgame.starter_duel_winner);

  return (
    <section className="space-y-4">
      <header className="rounded-xl border border-neutral-200 bg-gradient-to-b from-white to-neutral-50 p-5 text-center">
        <p className="font-mono text-[10px] font-semibold uppercase tracking-[0.16em] text-green-600">Final</p>
        <div className="mt-3 flex items-center justify-center gap-4">
          <TeamBadge abbreviation={matchup.teams.away.abbreviation} size={34} />
          <h2 className="text-3xl font-bold tracking-tight text-neutral-900" style={{ fontVariantNumeric: "tabular-nums" }}>
            {teamLabel(matchup.teams.away)} {postgame.final_score.away_team_runs}{" "}
            <span className="text-neutral-300">-</span> {teamLabel(matchup.teams.home)} {postgame.final_score.home_team_runs}
          </h2>
          <TeamBadge abbreviation={matchup.teams.home.abbreviation} size={34} />
        </div>
      </header>

      <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
        <StarterCard
          starter={matchup.starters.away_starter}
          teamName={matchup.teams.away.name}
          side="away"
          mode="postgame"
          starterLine={postgame.starter_lines.away_starter}
        />
        <StarterCard
          starter={matchup.starters.home_starter}
          teamName={matchup.teams.home.name}
          side="home"
          mode="postgame"
          starterLine={postgame.starter_lines.home_starter}
        />
      </div>

      <div className="flex items-center justify-center gap-2.5 rounded-xl border border-neutral-200 bg-gradient-to-b from-white to-neutral-50 px-4 py-3.5">
        {winnerAbbr ? <TeamBadge abbreviation={winnerAbbr} size={24} fontSize={9} /> : null}
        <span className="text-sm font-semibold text-neutral-900">Starter duel: {postgame.starter_duel_winner}</span>
        <span className="rounded-md bg-green-100 px-2 py-1 font-mono text-[9px] font-semibold uppercase tracking-wide text-green-800">
          Winner
        </span>
      </div>

      <section className="grid grid-cols-1 gap-3 md:grid-cols-2">
        <ExecutionBlock team={matchup.teams.away.abbreviation} line={postgame.starter_lines.away_starter} />
        <ExecutionBlock team={matchup.teams.home.abbreviation} line={postgame.starter_lines.home_starter} />
      </section>

      <CallCheck callCheck={postgame.call_check} />
      <CriticReviewPanel criticReview={matchup.critic_review} />
    </section>
  );
}

function ExecutionBlock({
  team,
  line,
}: {
  team: string | null;
  line: NonNullable<Matchup["postgame"]>["starter_lines"]["away_starter"];
}) {
  const teamColor = getTeamColor(team);
  return (
    <article
      className="rounded-xl border border-neutral-200 border-t-[3px] bg-white p-4"
      style={{ borderTopColor: teamColor.bg }}
    >
      <div className="flex items-center gap-2.5">
        <TeamBadge abbreviation={team} size={22} />
        <h3 className="text-[15px] font-bold text-neutral-900">{line.name}</h3>
      </div>
      <p className="mt-3.5 font-mono text-[10px] font-semibold uppercase tracking-wide text-neutral-400">Plan vs execution</p>
      <p className="mt-1.5 text-[13px] leading-6 text-neutral-600">{line.plan_vs_execution}</p>
      <p className="mt-3.5 font-mono text-[10px] font-semibold uppercase tracking-wide text-neutral-400">What to watch next</p>
      <p className="mt-1.5 text-[13px] leading-6 text-neutral-600">{line.what_to_watch_next}</p>
    </article>
  );
}

function PitchLegend({ matchup }: { matchup: Matchup }) {
  const pitches = Array.from(new Set(matchup.charts.pitch_mix.map((row) => row.pitch)));

  return (
    <div className="flex flex-wrap gap-4 rounded-xl border border-neutral-100 bg-neutral-50 px-4 py-3">
      {pitches.map((pitch) => (
        <span key={pitch} className="flex items-center gap-1.5 text-[12px] font-medium text-neutral-600">
          <span className="h-2 w-2 rounded-full" style={{ backgroundColor: getPitchColor(pitch) }} />
          {pitch}
        </span>
      ))}
    </div>
  );
}

function findStarterSection(sections: ReportSection[], fallbackName: string, starterName: string) {
  return sections.find((section) => section.title.includes(starterName)) ??
    sections.find((section) => section.title.includes(fallbackName));
}

function teamAbbrForName(matchup: Matchup, starterName: string) {
  if (matchup.starters.away_starter.name === starterName) return matchup.teams.away.abbreviation;
  if (matchup.starters.home_starter.name === starterName) return matchup.teams.home.abbreviation;
  return null;
}
