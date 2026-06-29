"use client";

import type { ArchiveItem, Matchup } from "@/lib/types";

interface GameCarouselProps {
  matchups: Matchup[];
  archive: ArchiveItem[];
  featuredId: string;
}

export default function GameCarousel({ matchups, archive, featuredId }: GameCarouselProps) {
  return (
    <section className="space-y-3">
      <div className="flex items-center justify-between gap-3">
        <h2 className="text-sm font-bold uppercase tracking-widest text-neutral-500">Games</h2>
        <span className="text-xs text-neutral-500">{archive.length} archived</span>
      </div>
      <div className="flex snap-x gap-3 overflow-x-auto pb-2">
        {matchups.map((matchup) => {
          const isFeatured = matchup.id === featuredId;
          return (
            <button
              key={matchup.id}
              type="button"
              onClick={() => undefined}
              className={`min-w-[250px] snap-start rounded-xl border bg-white p-4 text-left transition hover:border-neutral-400 ${
                isFeatured ? "border-blue-700" : "border-neutral-200"
              }`}
            >
              <div className="flex items-center justify-between gap-2">
                <DateBadge date={matchup.date} />
                <span className={`rounded-full px-2 py-1 text-[10px] font-bold uppercase tracking-wide ${statusClass(matchup.status, isFeatured)}`}>
                  {isFeatured ? "recommended" : matchup.status}
                </span>
              </div>
              <p className="mt-3 font-bold text-neutral-900">
                {matchup.teams.away.abbreviation} @ {matchup.teams.home.abbreviation}
              </p>
              <p className="mt-1 text-sm text-neutral-500">
                {matchup.status === "final" && matchup.postgame
                  ? `${matchup.teams.away.abbreviation} ${matchup.postgame.final_score.away_team_runs} - ${matchup.teams.home.abbreviation} ${matchup.postgame.final_score.home_team_runs}`
                  : matchup.game.start_time_local}
              </p>
              <p className="mt-3 line-clamp-2 text-sm leading-5 text-neutral-600">
                {matchup.report.headline}
              </p>
            </button>
          );
        })}
      </div>
    </section>
  );
}

function DateBadge({ date }: { date: string }) {
  const today = new Date().toISOString().slice(0, 10);
  const label = date === today ? "Today" : date;
  return <span className="text-xs font-medium text-neutral-500">{label}</span>;
}

function statusClass(status: Matchup["status"], featured: boolean) {
  if (featured) return "bg-blue-100 text-blue-700";
  if (status === "final") return "bg-green-100 text-green-800";
  if (status === "upcoming") return "bg-neutral-100 text-neutral-600";
  return "bg-neutral-100 text-neutral-600";
}
