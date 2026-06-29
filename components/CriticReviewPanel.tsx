import type { CriticCheckStatus, CriticReview } from "@/lib/types";

interface CriticReviewPanelProps {
  criticReview: CriticReview;
}

const statusClasses: Record<CriticCheckStatus, string> = {
  supported: "bg-green-100 text-green-800",
  revised: "bg-amber-100 text-amber-800",
  warning: "bg-amber-100 text-amber-800",
  unsupported: "bg-red-100 text-red-800",
  not_present: "bg-neutral-100 text-neutral-600",
};

export default function CriticReviewPanel({ criticReview }: CriticReviewPanelProps) {
  return (
    <section className="rounded-xl border border-neutral-200 bg-white p-4">
      <p className="text-xs font-semibold uppercase tracking-widest text-blue-700">Critic Review</p>
      <h2 className="mt-2 text-xl font-bold text-neutral-900">Claims Checked</h2>
      <p className="mt-2 text-sm leading-6 text-neutral-600">{criticReview.summary}</p>
      <div className="mt-4 space-y-3">
        {criticReview.checks.map((check) => (
          <article key={`${check.claim}-${check.status}`} className="rounded-lg bg-neutral-50 p-3">
            <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
              <p className="font-medium leading-6 text-neutral-900">{check.claim}</p>
              <span className={`w-fit rounded-full px-2.5 py-1 text-[11px] font-bold uppercase tracking-wide ${statusClasses[check.status]}`}>
                {check.status.replaceAll("_", " ")}
              </span>
            </div>
            <p className="mt-2 text-sm leading-6 text-neutral-600">{check.evidence}</p>
          </article>
        ))}
      </div>
      {criticReview.revision_notes.length > 0 ? (
        <div className="mt-4 rounded-lg border border-neutral-200 p-3">
          <h3 className="text-sm font-bold text-neutral-900">Revision Notes</h3>
          <ul className="mt-2 space-y-2 text-sm leading-6 text-neutral-600">
            {criticReview.revision_notes.map((note) => (
              <li key={note}>{note}</li>
            ))}
          </ul>
        </div>
      ) : null}
    </section>
  );
}
