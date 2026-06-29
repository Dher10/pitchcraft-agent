import type { Game, Team } from "@/lib/types";

interface MatchupSummaryProps {
  game: Game;
  teams: {
    away: Team;
    home: Team;
  };
}

export default function MatchupSummary({ game, teams }: MatchupSummaryProps) {
  return (
    <section className="grid gap-4 lg:grid-cols-[0.85fr_1.15fr]">
      <div className="rounded-lg border border-[#E5E8EC] bg-white p-5">
        <p className="text-sm font-semibold uppercase tracking-[0.16em] text-[#1B3A5B]">
          Game
        </p>
        <h3 className="mt-3 font-display text-2xl font-bold text-[#0F1722]">
          {game.venue}
        </h3>
        <dl className="mt-5 grid gap-3 text-sm">
          <Info label="First pitch" value={game.start_time_local} />
          <Info label="Timezone" value={game.timezone} />
          <Info label="Note" value={game.broadcast_note} />
        </dl>
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        <OffenseCard team={teams.away} />
        <OffenseCard team={teams.home} />
      </div>
    </section>
  );
}

function Info({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-baseline justify-between gap-4 border-b border-[#E5E8EC] pb-3 last:border-b-0 last:pb-0">
      <dt className="text-[#5B6573]">{label}</dt>
      <dd className="text-right font-semibold text-[#0F1722]">{value}</dd>
    </div>
  );
}

function OffenseCard({ team }: { team: Team }) {
  const profile = team.offense_profile;

  return (
    <article className="rounded-lg border border-[#E5E8EC] bg-white p-5">
      <p className="text-sm font-semibold uppercase tracking-[0.16em] text-[#1B3A5B]">
        {team.abbreviation} offense
      </p>
      <h3 className="mt-3 min-h-14 text-lg font-bold leading-7 text-[#0F1722]">
        {profile.summary_label}
      </h3>
      <dl className="mt-5 grid grid-cols-2 gap-3 text-sm">
        <Metric label="Split" value={profile.vs_pitcher_hand} />
        <Metric label="Recent" value={profile.recent_form} />
        <Metric label="OPS" value={profile.ops_vs_hand} />
        <Metric label="K rate" value={profile.k_rate_vs_hand} />
        <Metric label="BB rate" value={profile.bb_rate_vs_hand} />
      </dl>
    </article>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md bg-[#F7F8FA] p-3">
      <dt className="text-xs font-semibold uppercase tracking-[0.1em] text-[#5B6573]">
        {label}
      </dt>
      <dd className="tabular mt-1 font-display text-xl font-bold text-[#0F1722]">
        {value}
      </dd>
    </div>
  );
}
