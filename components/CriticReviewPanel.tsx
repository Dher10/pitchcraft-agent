import type { CriticCheckStatus, CriticReview } from "@/lib/types";

interface CriticReviewPanelProps {
  criticReview: CriticReview;
}

const statusClasses: Record<CriticCheckStatus, string> = {
  supported: "bg-green-100 text-green-800",
  warning: "bg-amber-100 text-amber-800",
  unsupported: "bg-red-100 text-red-800",
  not_present: "bg-neutral-100 text-neutral-500",
};

export default function CriticReviewPanel({ criticReview }: CriticReviewPanelProps) {
  return (
    <section className="rounded-xl border border-neutral-200 bg-white p-4">
      <p className="font-mono text-[11px] font-semibold uppercase tracking-widest text-blue-600">Critic Review</p>
      <h2 className="mt-1.5 text-lg font-bold text-neutral-900">Claims Checked</h2>
      <p className="mt-1.5 text-[13px] leading-6 text-neutral-500">{criticReview.summary}</p>
      <div className="mt-4 space-y-2.5">
        {criticReview.checks.map((check) => (
          <article key={`${check.claim}-${check.status}`} className="rounded-lg bg-neutral-50 p-3">
            <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
              <p className="text-[13px] font-semibold leading-5 text-neutral-800">{check.claim}</p>
              <span className={`w-fit shrink-0 rounded-md px-2 py-1 font-mono text-[9px] font-semibold uppercase tracking-wide ${statusClasses[check.status]}`}>
                {check.status.replaceAll("_", " ")}
              </span>
            </div>
            <p className="mt-1.5 text-[12px] leading-5 text-neutral-500">{check.evidence}</p>
          </article>
        ))}
      </div>
      {criticReview.revision_notes.length > 0 ? (
        <div className="mt-3.5 rounded-lg border border-neutral-100 bg-neutral-50 p-3">
          <h3 className="font-mono text-[10px] font-semibold uppercase tracking-widest text-neutral-400">Critic Notes</h3>
          <ul className="mt-2 space-y-1.5 text-[12px] leading-5 text-neutral-600">
            {criticReview.revision_notes.map((note) => (
              <li key={note}>{note}</li>
            ))}
          </ul>
        </div>
      ) : null}
    </section>
  );
}
