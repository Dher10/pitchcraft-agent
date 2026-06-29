import type { CriticCheckStatus, CriticReview } from "@/lib/types";

interface CriticReviewPanelProps {
  review: CriticReview;
}

const chipClasses: Record<CriticCheckStatus, string> = {
  supported: "border-[#B7E0C8] bg-[#EAF7EF] text-[#1E7A46]",
  revised: "border-[#F2D58B] bg-[#FFF5D6] text-[#9A6B00]",
  warning: "border-[#F2D58B] bg-[#FFF5D6] text-[#9A6B00]",
  unsupported: "border-[#F5B8B2] bg-[#FDEDEC] text-[#B42318]",
  not_present: "border-[#D5DAE1] bg-[#F2F4F7] text-[#475467]",
};

export default function CriticReviewPanel({ review }: CriticReviewPanelProps) {
  return (
    <section className="rounded-lg border-2 border-[#1B3A5B] bg-white p-5 shadow-sm sm:p-7">
      <div className="flex flex-col justify-between gap-4 md:flex-row md:items-start">
        <div>
          <p className="text-sm font-semibold uppercase tracking-[0.16em] text-[#1B3A5B]">
            Reviewed against data
          </p>
          <h2 className="mt-3 font-display text-3xl font-black text-[#0F1722]">
            Critic Review
          </h2>
          <p className="mt-2 max-w-3xl text-base leading-7 text-[#5B6573]">
            {review.summary}
          </p>
        </div>
        <span className="w-fit rounded-full bg-[#1B3A5B] px-3 py-1.5 text-xs font-bold uppercase tracking-[0.12em] text-white">
          {review.status}
        </span>
      </div>

      <div className="mt-7 grid gap-4">
        {review.checks.map((check) => (
          <article
            key={`${check.claim}-${check.status}`}
            className="rounded-lg border border-[#E5E8EC] bg-[#F7F8FA] p-4"
          >
            <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
              <h3 className="text-base font-bold leading-7 text-[#0F1722]">
                {check.claim}
              </h3>
              <span
                className={`w-fit shrink-0 rounded-full border px-3 py-1 text-xs font-bold uppercase tracking-[0.1em] ${chipClasses[check.status]}`}
              >
                {check.status.replaceAll("_", " ")}
              </span>
            </div>
            <p className="mt-3 border-l-2 border-[#1B3A5B] pl-3 text-sm leading-6 text-[#5B6573]">
              {check.evidence}
            </p>
          </article>
        ))}
      </div>

      <div className="mt-7 rounded-lg bg-[#0F1722] p-5 text-white">
        <h3 className="font-display text-xl font-bold">Revision Notes</h3>
        <ul className="mt-3 grid gap-2 text-sm leading-6 text-[#D5DAE1]">
          {review.revision_notes.map((note) => (
            <li key={note} className="flex gap-3">
              <span className="mt-3 h-1.5 w-1.5 shrink-0 rounded-full bg-[#C8D7E6]" />
              <span>{note}</span>
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}
