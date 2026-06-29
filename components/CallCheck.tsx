import type { CallCheckItem, CallResult } from "@/lib/types";

interface CallCheckProps {
  callCheck: CallCheckItem[];
}

const resultClasses: Record<CallResult, string> = {
  held_up: "bg-green-100 text-green-800",
  partially_held_up: "bg-amber-100 text-amber-800",
  did_not_hold_up: "bg-red-100 text-red-800",
  unclear: "bg-neutral-100 text-neutral-600",
};

const resultLabels: Record<CallResult, string> = {
  held_up: "HELD UP",
  partially_held_up: "PARTIALLY",
  did_not_hold_up: "DID NOT HOLD UP",
  unclear: "UNCLEAR",
};

export default function CallCheck({ callCheck }: CallCheckProps) {
  return (
    <section className="rounded-xl border border-neutral-200 bg-white p-4">
      <h2 className="text-xl font-bold text-neutral-900">Call Check</h2>
      <div className="mt-4 space-y-3">
        {callCheck.map((item) => (
          <article key={`${item.pregame_note}-${item.result}`} className="rounded-lg bg-neutral-50 p-3">
            <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
              <p className="font-medium leading-6 text-neutral-900">{item.pregame_note}</p>
              <span className={`w-fit rounded-full px-2.5 py-1 text-[11px] font-bold uppercase tracking-wide ${resultClasses[item.result]}`}>
                {resultLabels[item.result]}
              </span>
            </div>
            <p className="mt-2 text-sm leading-6 text-neutral-600">{item.postgame_evidence}</p>
          </article>
        ))}
      </div>
    </section>
  );
}
