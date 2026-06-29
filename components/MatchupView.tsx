"use client";

import { useState } from "react";
import CallCheck from "@/components/CallCheck";
import CriticReviewPanel from "@/components/CriticReviewPanel";
import DetailedAnalysis from "@/components/DetailedAnalysis";
import ScoutingReport from "@/components/ScoutingReport";
import StarterCard from "@/components/StarterCard";
import { getPitchColor } from "@/components/ZoneDiagram";
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
        <p className="text-sm text-neutral-500">
          {matchup.game.venue} - {matchup.game.start_time_local} {matchup.game.timezone}
        </p>
        <h2 className="mt-2 text-2xl font-bold text-neutral-900">{matchup.report.headline}</h2>
        <p className="mt-3 text-sm leading-6 text-neutral-600">{matchup.report.short_summary[0]}</p>
      </header>

      <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
        <StarterCard
          starter={matchup.starters.away_starter}
          side="away"
          mode="pregame"
          locations={matchup.pitch_locations.away_starter.vs_rhh}
        />
        <StarterCard
          starter={matchup.starters.home_starter}
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
          <h2 className="text-xl font-bold text-neutral-900">What to watch</h2>
          <div className="mt-3 space-y-2 text-sm leading-6 text-neutral-600">
            {watchSection.bullets.map((bullet) => (
              <p key={bullet}>{bullet}</p>
            ))}
          </div>
        </section>
      ) : null}

      <button
        type="button"
        onClick={() => setShowDetails((current) => !current)}
        className="w-full rounded-xl border border-blue-700 bg-white px-4 py-3 text-sm font-bold text-blue-700 transition hover:bg-blue-50"
      >
        {showDetails ? "Hide detailed analysis" : "See detailed analysis"}
      </button>

      {showDetails ? <DetailedAnalysis matchup={matchup} /> : null}
      <CriticReviewPanel criticReview={matchup.critic_review} />
    </section>
  );
}

function PostgameMode({ matchup }: { matchup: Matchup }) {
  const postgame = matchup.postgame;

  if (!postgame) return null;

  return (
    <section className="space-y-4">
      <header className="rounded-xl border border-neutral-200 bg-white p-4 text-center">
        <p className="text-xs font-semibold uppercase tracking-widest text-neutral-500">Final</p>
        <h2 className="mt-2 text-3xl font-bold text-neutral-900" style={{ fontVariantNumeric: "tabular-nums" }}>
          {matchup.teams.away.abbreviation} {postgame.final_score.away_team_runs} - {matchup.teams.home.abbreviation} {postgame.final_score.home_team_runs}
        </h2>
      </header>

      <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
        <StarterCard
          starter={matchup.starters.away_starter}
          side="away"
          mode="postgame"
          starterLine={postgame.starter_lines.away_starter}
        />
        <StarterCard
          starter={matchup.starters.home_starter}
          side="home"
          mode="postgame"
          starterLine={postgame.starter_lines.home_starter}
        />
      </div>

      <p className="rounded-xl border border-neutral-200 bg-white p-4 text-center font-bold text-neutral-900">
        Starter duel: {postgame.starter_duel_winner}
      </p>

      <section className="grid grid-cols-1 gap-3 md:grid-cols-2">
        <ExecutionBlock line={postgame.starter_lines.away_starter} />
        <ExecutionBlock line={postgame.starter_lines.home_starter} />
      </section>

      <CallCheck callCheck={postgame.call_check} />
      <CriticReviewPanel criticReview={matchup.critic_review} />
    </section>
  );
}

function ExecutionBlock({ line }: { line: NonNullable<Matchup["postgame"]>["starter_lines"]["away_starter"] }) {
  return (
    <article className="rounded-xl border border-neutral-200 bg-white p-4">
      <h3 className="font-bold text-neutral-900">{line.name}</h3>
      <p className="mt-3 text-sm font-semibold text-neutral-700">Plan vs execution</p>
      <p className="mt-1 text-sm leading-6 text-neutral-600">{line.plan_vs_execution}</p>
      <p className="mt-3 text-sm font-semibold text-neutral-700">What to watch next</p>
      <p className="mt-1 text-sm leading-6 text-neutral-600">{line.what_to_watch_next}</p>
    </article>
  );
}

function PitchLegend({ matchup }: { matchup: Matchup }) {
  const pitches = Array.from(new Set(matchup.charts.pitch_mix.map((row) => row.pitch)));

  return (
    <div className="flex flex-wrap gap-3 rounded-xl border border-neutral-200 bg-white p-4">
      {pitches.map((pitch) => (
        <span key={pitch} className="flex items-center gap-2 text-xs font-medium text-neutral-600">
          <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: getPitchColor(pitch) }} />
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
