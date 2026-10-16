import { formatModeLine } from "@/lib/format";

interface ModeLineProps {
  dataMode: string;
  fetchedAt: string | null | undefined;
}

// Rule 6: the page says whether it shows live or demo data. Live only for a fetched snapshot.
export default function ModeLine({ dataMode, fetchedAt }: ModeLineProps) {
  const live = dataMode === "fetched_snapshot";
  return (
    <p
      data-testid="mode-line"
      data-mode={live ? "live" : "demo"}
      className={`mb-3 inline-flex items-center gap-2 rounded-md px-2 py-1 font-mono text-[10px] font-semibold uppercase tracking-[0.12em] ${
        live ? "bg-green-50 text-green-800" : "bg-amber-50 text-amber-800"
      }`}
    >
      <span aria-hidden="true" className={`h-1.5 w-1.5 rounded-full ${live ? "bg-green-600" : "bg-amber-500"}`} />
      {formatModeLine(dataMode, fetchedAt)}
    </p>
  );
}
