import type { ReportSection, Starter, Team } from "@/lib/types";

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
        title={`${awayStarter.name} vs ${awayOpponent.abbreviation}`}
        section={awaySection}
        offense={awayOpponent}
      />
      <ReportCard
        title={`${homeStarter.name} vs ${homeOpponent.abbreviation}`}
        section={homeSection}
        offense={homeOpponent}
      />
    </section>
  );
}

function ReportCard({ title, section, offense }: { title: string; section?: ReportSection; offense: Team }) {
  return (
    <article className="rounded-xl border border-neutral-200 bg-white p-4">
      <h3 className="font-bold text-neutral-900">{title}</h3>
      <p className="mt-2 text-sm leading-6 text-neutral-600">
        {section?.body ?? offense.offense_profile.summary_label}
      </p>
      <dl className="mt-4 grid grid-cols-3 gap-2 text-xs" style={{ fontVariantNumeric: "tabular-nums" }}>
        <Metric label="OPS" value={offense.offense_profile.ops_vs_hand} />
        <Metric label="K" value={offense.offense_profile.k_rate_vs_hand} />
        <Metric label="BB" value={offense.offense_profile.bb_rate_vs_hand} />
      </dl>
      <p className="mt-3 text-xs text-neutral-500">
        vs {offense.offense_profile.vs_pitcher_hand} - {offense.offense_profile.recent_form}
      </p>
    </article>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  const title = label === "OPS" ? "On-base plus slugging." : label === "K" ? "Strikeout rate." : "Walk rate.";
  return (
    <div className="rounded-lg bg-neutral-50 p-2">
      <dt className="font-semibold text-neutral-500">
        <span title={title} className="cursor-help border-b border-dotted border-neutral-400">
          {label}
        </span>
      </dt>
      <dd className="mt-1 font-bold text-neutral-900">{value}</dd>
    </div>
  );
}
