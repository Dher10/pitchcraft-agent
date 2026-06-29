import type { DataConfidence, Game, MatchupStatus, Report, Starter, Team } from "@/lib/types";

interface FeaturedMatchupCardProps {
  date: string;
  status: MatchupStatus;
  game: Game;
  teams: {
    away: Team;
    home: Team;
  };
  starters: {
    away_starter: Starter;
    home_starter: Starter;
  };
  report: Report;
  dataConfidence: DataConfidence;
}

const statusTone: Record<MatchupStatus, string> = {
  upcoming: "border-[#C9D3DE] bg-[#EEF3F8] text-[#1B3A5B]",
  final: "border-[#B7E0C8] bg-[#EAF7EF] text-[#1E7A46]",
  demo: "border-[#D5DAE1] bg-[#F2F4F7] text-[#475467]",
};

export default function FeaturedMatchupCard({
  date,
  status,
  game,
  teams,
  starters,
  report,
  dataConfidence,
}: FeaturedMatchupCardProps) {
  return (
    <section className="rounded-lg border border-[#E5E8EC] bg-white p-5 sm:p-7">
      <div className="flex flex-col justify-between gap-5 lg:flex-row lg:items-start">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <span
              className={`rounded-full border px-3 py-1 text-xs font-bold uppercase tracking-[0.12em] ${statusTone[status]}`}
            >
              {status}
            </span>
            <span className="tabular text-sm font-medium text-[#5B6573]">
              {date}
            </span>
          </div>
          <h2 className="mt-5 font-display text-3xl font-black leading-tight text-[#0F1722] sm:text-4xl">
            {game.title}
          </h2>
          <p className="mt-3 max-w-3xl text-lg leading-8 text-[#5B6573]">
            {report.headline}
          </p>
        </div>
        <div className="rounded-lg border border-[#E5E8EC] bg-[#F7F8FA] p-4 text-sm">
          <p className="font-semibold text-[#0F1722]">Data confidence</p>
          <p className="mt-2 inline-flex rounded-full bg-white px-2.5 py-1 text-xs font-bold uppercase tracking-[0.12em] text-[#1B3A5B] ring-1 ring-[#E5E8EC]">
            {dataConfidence.level.replaceAll("_", " ")}
          </p>
          <p className="mt-3 text-[#5B6573]">
            Pitch data: {dataConfidence.pitch_data_status}
          </p>
        </div>
      </div>

      <div className="mt-7 grid gap-4 md:grid-cols-[1fr_auto_1fr] md:items-center">
        <TeamBlock team={teams.away} starter={starters.away_starter} />
        <div className="hidden h-px bg-[#E5E8EC] md:block md:h-20 md:w-px" />
        <TeamBlock team={teams.home} starter={starters.home_starter} alignRight />
      </div>
    </section>
  );
}

function TeamBlock({
  team,
  starter,
  alignRight = false,
}: {
  team: Team;
  starter: Starter;
  alignRight?: boolean;
}) {
  return (
    <div className={alignRight ? "md:text-right" : undefined}>
      <p className="font-display text-2xl font-black text-[#0F1722]">
        {team.abbreviation}
      </p>
      <p className="mt-1 font-semibold text-[#0F1722]">{team.name}</p>
      <p className="tabular mt-1 text-sm text-[#5B6573]">{team.record}</p>
      <p className="mt-3 text-sm text-[#5B6573]">
        Starter:{" "}
        <span className="font-semibold text-[#0F1722]">{starter.name}</span>
      </p>
    </div>
  );
}
