"use client";

import TeamBadge from "@/components/TeamBadge";
import { UNAVAILABLE, formatStartTime, todayInNewYork } from "@/lib/format";
import { getTeamColor } from "@/lib/teamColors";
import { teamLabel } from "@/lib/teamLabel";
import type { ArchiveItem, Matchup } from "@/lib/types";

interface GameCarouselProps {
  matchups: Matchup[];
  archive: ArchiveItem[];
  featuredId: string | null;
  selectedId: string;
  onSelect: (matchupId: string) => void;
  /** Today in New York as YYYY-MM-DD; the clock when absent (tests give it). */
  today?: string;
}

export default function GameCarousel({
  matchups,
  archive,
  featuredId,
  selectedId,
  onSelect,
  today,
}: GameCarouselProps) {
  const todayDate = today ?? todayInNewYork();
  return (
    <section className="space-y-3">
      <div className="flex items-baseline justify-between gap-3">
        <h2 className="font-mono text-[11px] font-semibold uppercase tracking-widest text-neutral-400">Games</h2>
        <span className="text-xs text-neutral-400">{archive.length} archived</span>
      </div>
      <div className="flex snap-x gap-3.5 overflow-x-auto pb-2">
        {matchups.map((matchup) => {
          const isFeatured = matchup.id === featuredId;
          const isSelected = matchup.id === selectedId;
          const awayColor = getTeamColor(matchup.teams.away.abbreviation);
          const homeColor = getTeamColor(matchup.teams.home.abbreviation);
          return (
            <button
              key={matchup.id}
              type="button"
              onClick={() => onSelect(matchup.id)}
              className={`min-w-[230px] snap-start overflow-hidden rounded-xl border bg-white text-left transition hover:-translate-y-0.5 hover:shadow-lg ${
                isSelected
                  ? "border-blue-600 shadow-[0_4px_16px_-8px_rgba(37,99,235,0.35)]"
                  : isFeatured
                    ? "border-blue-200 shadow-[0_4px_16px_-8px_rgba(37,99,235,0.28)]"
                    : "border-neutral-200 shadow-[0_1px_2px_rgba(0,0,0,0.04)]"
              }`}
            >
              <div
                className="h-1"
                style={{ background: `linear-gradient(90deg, ${awayColor.bg} 0 50%, ${homeColor.bg} 50% 100%)` }}
              />
              <div className="px-3.5 pb-4 pt-3">
                <div className="flex items-center justify-between gap-2">
                  <DateBadge date={matchup.date} today={todayDate} />
                  <span className={`rounded-md px-1.5 py-1 font-mono text-[9px] font-semibold uppercase tracking-wide ${statusClass(matchup.status, isFeatured)}`}>
                    {isFeatured ? "recommended" : statusLabel(matchup.status)}
                  </span>
                </div>
                <div className="mt-3 flex items-center gap-2">
                  <TeamBadge abbreviation={matchup.teams.away.abbreviation} size={26} />
                  <p className="font-semibold text-neutral-900">
                    {teamLabel(matchup.teams.away)}
                    <span className="mx-1 font-normal text-neutral-400">@</span>
                    {teamLabel(matchup.teams.home)}
                  </p>
                  <TeamBadge abbreviation={matchup.teams.home.abbreviation} size={26} />
                </div>
                <p className="mt-2.5 font-mono text-[10px] text-neutral-400">
                  {matchup.status === "final" && matchup.postgame
                    ? `${teamLabel(matchup.teams.away)} ${matchup.postgame.final_score.away_team_runs} - ${teamLabel(matchup.teams.home)} ${matchup.postgame.final_score.home_team_runs}`
                    : formatStartTime(matchup.game)}
                </p>
                <p className="mt-2 line-clamp-2 text-[13px] leading-5 text-neutral-600">
                  {matchup.report.headline}
                </p>
              </div>
            </button>
          );
        })}
      </div>
    </section>
  );
}

function DateBadge({ date, today }: { date: string; today: string }) {
  const label = date === today ? "Today" : date;
  return <span className="font-mono text-[11px] font-medium text-neutral-400">{label}</span>;
}

/**
 * What the badge says of the game: its state, or the dash of every unavailable figure when the schedule did not give one
 * (never a guessed "upcoming"). The dash is the page's existing way to say "not available": no new wording.
 */
export function statusLabel(status: Matchup["status"]): string {
  return status ?? UNAVAILABLE;
}

function statusClass(status: Matchup["status"], featured: boolean) {
  if (featured) return "bg-blue-600 text-white";
  if (status === "final") return "bg-green-100 text-green-800";
  if (status === "live") return "bg-amber-100 text-amber-800";
  return "border border-neutral-200 bg-neutral-100 text-neutral-500";
}
