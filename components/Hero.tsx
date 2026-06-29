import type { AgentWorkflow, Metadata } from "@/lib/types";

interface HeroProps {
  metadata: Metadata;
  workflow: AgentWorkflow;
}

export default function Hero({ metadata, workflow }: HeroProps) {
  return (
    <header className="mx-auto flex w-full max-w-6xl flex-col gap-8 px-5 pb-10 pt-8 sm:px-8 lg:px-10">
      <div className="flex flex-col justify-between gap-6 border-b border-[#E5E8EC] pb-8 md:flex-row md:items-end">
        <div className="max-w-3xl">
          <p className="mb-4 text-sm font-semibold uppercase tracking-[0.18em] text-[#1B3A5B]">
            Cached Demo
          </p>
          <h1 className="font-display text-4xl font-black leading-tight text-[#0F1722] sm:text-6xl">
            {metadata.project_name}
          </h1>
          <p className="mt-5 max-w-2xl text-lg leading-8 text-[#5B6573]">
            A fan-friendly scouting report for a daily starting-pitcher
            matchup.
          </p>
          <p className="mt-3 max-w-2xl text-base leading-7 text-[#5B6573]">
            Cached matchup data becomes a readable report, then a critic checks
            the claims against the same data.
          </p>
        </div>
        <div className="rounded-lg border border-[#E5E8EC] bg-white px-5 py-4 text-sm text-[#5B6573]">
          <p className="font-semibold text-[#0F1722]">Milestone 1</p>
          <p>{metadata.last_updated_label}</p>
          <p className="mt-2 tabular text-xs uppercase tracking-[0.12em] text-[#475467]">
            Version {metadata.version}
          </p>
        </div>
      </div>

      <section aria-labelledby="workflow-heading" className="space-y-4">
        <div>
          <p className="text-sm font-semibold uppercase tracking-[0.16em] text-[#1B3A5B]">
            How PitchCraft Works
          </p>
          <h2
            id="workflow-heading"
            className="mt-2 font-display text-2xl font-bold text-[#0F1722]"
          >
            One clean pipeline from data to review
          </h2>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-[#5B6573]">
            {workflow.description}
          </p>
        </div>
        <ol className="grid gap-3 md:grid-cols-5">
          {workflow.steps.map((step, index) => (
            <li
              key={step.agent}
              className="rounded-lg border border-[#C9D3DE] bg-[#1B3A5B] p-4 text-white shadow-sm transition hover:-translate-y-0.5 motion-reduce:transition-none motion-reduce:hover:translate-y-0"
            >
              <span className="tabular text-xs font-bold text-[#C8D7E6]">
                {String(index + 1).padStart(2, "0")}
              </span>
              <h3 className="mt-3 min-h-12 text-sm font-bold leading-5">
                {step.agent.replace(" Agent", "")}
              </h3>
              <p className="mt-3 inline-flex rounded-full bg-white/12 px-2 py-1 text-xs font-semibold uppercase tracking-[0.1em] text-white">
                {step.status.replaceAll("_", " ")}
              </p>
              <p className="mt-3 text-xs leading-5 text-[#DCE8F2]">
                {step.output}
              </p>
            </li>
          ))}
        </ol>
      </section>
    </header>
  );
}
