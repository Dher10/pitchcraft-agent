import type { Starter } from "@/lib/types";

interface StarterCardProps {
  starter: Starter;
}

export default function StarterCard({ starter }: StarterCardProps) {
  const summary = starter.season_summary;
  const profile = starter.pitching_profile;

  return (
    <article className="rounded-lg border border-[#E5E8EC] bg-white p-5">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-sm font-semibold uppercase tracking-[0.16em] text-[#1B3A5B]">
            {starter.team} starter
          </p>
          <h3 className="mt-3 font-display text-3xl font-black leading-tight text-[#0F1722]">
            {starter.name}
          </h3>
          <p className="mt-2 text-sm font-semibold text-[#5B6573]">
            {starter.throws} · {profile.style_label}
          </p>
        </div>
      </div>

      <dl className="mt-6 grid grid-cols-3 gap-3">
        <Stat label="ERA" value={summary.era} />
        <Stat label="WHIP" value={summary.whip} />
        <Stat label="K" value={String(summary.strikeouts)} />
      </dl>

      <dl className="mt-5 grid gap-3 text-sm">
        <Detail label="Primary pitch" value={profile.primary_pitch} />
        <Detail label="Put-away pitch" value={profile.putaway_pitch} />
        <Detail label="Command" value={profile.command_label} />
        <Detail label="Swing/miss" value={profile.swing_miss_label} />
        <Detail label="Contact risk" value={profile.contact_risk_label} />
      </dl>

      <div className="mt-5 rounded-md bg-[#F7F8FA] p-4">
        <p className="text-sm font-bold text-[#0F1722]">
          {starter.recent_form.label}
        </p>
        <p className="mt-1 text-sm leading-6 text-[#5B6573]">
          {starter.recent_form.last_three_starts_summary}
        </p>
      </div>
    </article>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-[#E5E8EC] p-3">
      <dt className="text-xs font-semibold uppercase tracking-[0.12em] text-[#5B6573]">
        {label}
      </dt>
      <dd className="tabular mt-2 font-display text-2xl font-black text-[#0F1722]">
        {value}
      </dd>
    </div>
  );
}

function Detail({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-baseline justify-between gap-4 border-b border-[#E5E8EC] pb-3 last:border-b-0 last:pb-0">
      <dt className="text-[#5B6573]">{label}</dt>
      <dd className="text-right font-semibold text-[#0F1722]">{value}</dd>
    </div>
  );
}
