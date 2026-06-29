import type { AgentStatus, AgentWorkflow } from "@/lib/types";

interface AgentPipelineProps {
  workflow: AgentWorkflow;
}

const statusClasses: Record<AgentStatus, string> = {
  completed: "bg-green-100 text-green-800",
  not_applicable: "bg-neutral-100 text-neutral-600",
  pending: "bg-amber-100 text-amber-800",
};

export default function AgentPipeline({ workflow }: AgentPipelineProps) {
  return (
    <section className="rounded-xl border border-neutral-200 bg-white p-4">
      <h2 className="text-xl font-bold text-neutral-900">How PitchCraft Works</h2>
      <p className="mt-2 text-sm leading-6 text-neutral-600">{workflow.description}</p>
      <div className="mt-4 space-y-3">
        {workflow.steps.map((step) => (
          <article key={step.agent} className="rounded-lg bg-neutral-50 p-3">
            <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
              <h3 className="font-bold text-neutral-900">{step.agent}</h3>
              <span className={`w-fit rounded-full px-2.5 py-1 text-[11px] font-bold uppercase tracking-wide ${statusClasses[step.status]}`}>
                {step.status.replaceAll("_", " ")}
              </span>
            </div>
            <p className="mt-2 text-sm leading-6 text-neutral-600">{step.output}</p>
          </article>
        ))}
      </div>
    </section>
  );
}
