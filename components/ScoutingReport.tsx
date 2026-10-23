import StatTile from "@/components/StatTile";
import TeamBadge from "@/components/TeamBadge";
import { teamLabel } from "@/lib/teamLabel";
import type { ReportSection, Starter, Team } from "@/lib/types";

const UNAVAILABLE = "—";

interface ScoutingReportProps {
  awayStarter: Starter;
  homeStarter: Starter;
  awayOpponent: Team;
  homeOpponent: Team;
  awaySection?: ReportSection;
  homeSection?: ReportSection;
}

export default function ScoutingReport({
  awayStarter,
  homeStarter,
  awayOpponent,
  homeOpponent,
  awaySection,
  homeSection,
}: ScoutingReportProps) {
  return (
    <section className="grid grid-cols-1 gap-3 md:grid-cols-2">
      <ReportCard
        team={awayStarter.team}
        title={`${awayStarter.name} vs ${teamLabel(awayOpponent)}`}
        section={awaySection}
        offense={awayOpponent}
      />
      <ReportCard
        team={homeStarter.team}
        title={`${homeStarter.name} vs ${teamLabel(homeOpponent)}`}
        section={homeSection}
        offense={homeOpponent}
      />
    </section>
  );
}

function ReportCard({
  team,
  title,
  section,
  offense,
}: {
  team: string | null;
  title: string;
  section?: ReportSection;
  offense: Team;
}) {
  return (
    <article className="rounded-xl border border-neutral-200 bg-white p-4">
      <div className="flex items-center gap-2.5">
        <TeamBadge abbreviation={team} size={22} />
        <h3 className="text-[15px] font-bold leading-tight text-neutral-900">{title}</h3>
      </div>
      <p className="mt-3 text-[13px] leading-6 text-neutral-600">
        {section?.body ?? offense.offense_profile.summary_label ?? "Offense data not available"}
      </p>
      <dl className="mt-3.5 grid grid-cols-3 gap-2">
        <StatTile label="OPS" title="On-base plus slugging." value={offense.offense_profile.ops_vs_hand ?? UNAVAILABLE} />
        <StatTile label="K%" title="Strikeout rate." value={offense.offense_profile.k_rate_vs_hand ?? UNAVAILABLE} />
        <StatTile label="BB%" title="Walk rate." value={offense.offense_profile.bb_rate_vs_hand ?? UNAVAILABLE} />
      </dl>
      <p className="mt-2.5 font-mono text-[10px] text-neutral-400">
        {offense.offense_profile.vs_pitcher_hand ? `vs ${offense.offense_profile.vs_pitcher_hand}` : null}
        {offense.offense_profile.vs_pitcher_hand && offense.offense_profile.recent_form ? <> &middot; </> : null}
        {offense.offense_profile.recent_form ?? null}
      </p>
    </article>
  );
}
