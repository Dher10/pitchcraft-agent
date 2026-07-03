import type { AgentStatus, AgentWorkflow } from "@/lib/types";

interface AgentPipelineProps {
  workflow: AgentWorkflow;
}

const statusClasses: Record<AgentStatus, string> = {
  completed: "bg-green-100 text-green-800",
  not_applicable: "bg-neutral-100 text-neutral-500",
  pending: "bg-amber-100 text-amber-800",
};

export default function AgentPipeline({ workflow }: AgentPipelineProps) {
  return (
    <section className="rounded-xl border border-neutral-200 bg-white p-4">
      <h2 className="text-lg font-bold text-neutral-900">How PitchCraft Works</h2>
      <p className="mt-1.5 text-[13px] leading-6 text-neutral-500">{workflow.description}</p>
      <div className="mt-4 space-y-2.5">
        {workflow.steps.map((step, index) => (
          <article
            key={step.agent}
            className="flex flex-col gap-2 rounded-lg border border-neutral-200 p-3.5 sm:flex-row sm:items-center sm:justify-between"
          >
            <div className="flex items-center gap-3">
              <span className="flex h-[26px] w-[26px] shrink-0 items-center justify-center rounded-lg bg-neutral-100 font-mono text-[11px] font-bold text-neutral-500">
                {index + 1}
              </span>
              <div>
                <h3 className="text-[13px] font-bold text-neutral-900">{step.agent}</h3>
                <p className="mt-0.5 text-[12px] leading-5 text-neutral-500">{step.output}</p>
              </div>
            </div>
            <span className={`w-fit shrink-0 rounded-md px-2 py-1 font-mono text-[9px] font-semibold uppercase tracking-wide ${statusClasses[step.status]}`}>
              {step.status.replaceAll("_", " ")}
            </span>
          </article>
        ))}
      </div>
    </section>
  );
}
