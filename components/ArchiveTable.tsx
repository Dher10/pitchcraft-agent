import type { ArchiveItem, MatchupStatus } from "@/lib/types";

interface ArchiveTableProps {
  archive: ArchiveItem[];
}

const statusClasses: Record<MatchupStatus, string> = {
  upcoming: "bg-neutral-100 text-neutral-500",
  live: "bg-amber-100 text-amber-800",
  final: "bg-green-100 text-green-800",
  demo: "bg-neutral-100 text-neutral-500",
};

export default function ArchiveTable({ archive }: ArchiveTableProps) {
  if (archive.length === 0) {
    return (
      <section className="rounded-xl border border-neutral-200 bg-white p-4">
        <h2 className="text-lg font-bold text-neutral-900">Archive</h2>
        <p className="mt-4 text-sm text-neutral-500">No past reports yet</p>
      </section>
    );
  }

  return (
    <section className="rounded-xl border border-neutral-200 bg-white p-4">
      <h2 className="text-lg font-bold text-neutral-900">Archive</h2>
      <div className="mt-4 overflow-x-auto">
        <table className="w-full min-w-[720px] border-collapse text-left text-sm">
          <thead>
            <tr className="border-b border-neutral-200 bg-neutral-50 font-mono text-[9px] uppercase tracking-widest text-neutral-400">
              <th className="py-2.5 pl-3 pr-3 font-semibold">Date</th>
              <th className="px-3 py-2.5 font-semibold">Matchup</th>
              <th className="px-3 py-2.5 font-semibold">Status</th>
              <th className="px-3 py-2.5 font-semibold">Starters</th>
              <th className="px-3 py-2.5 font-semibold">Result</th>
              <th className="py-2.5 pl-3 pr-3 font-semibold">Grade</th>
            </tr>
          </thead>
          <tbody>
            {archive.map((item) => (
              <tr key={item.id} className="border-b border-neutral-100 last:border-b-0">
                <td className="py-3 pl-3 pr-3 font-mono text-[12px] font-medium text-neutral-600" style={{ fontVariantNumeric: "tabular-nums" }}>
                  {item.date}
                </td>
                <td className="px-3 py-3 text-[13px] font-semibold text-neutral-900">
                  {item.title}
                  {item.featured ? (
                    <span className="ml-2 rounded-md bg-blue-50 px-1.5 py-0.5 font-mono text-[9px] font-semibold uppercase tracking-wide text-blue-600">
                      Featured
                    </span>
                  ) : null}
                </td>
                <td className="px-3 py-3">
                  <span className={`w-fit rounded-md px-2 py-1 font-mono text-[9px] font-semibold uppercase tracking-wide ${statusClasses[item.status]}`}>
                    {item.status}
                  </span>
                </td>
                <td className="px-3 py-3 text-[12px] text-neutral-500">{item.starter_summary}</td>
                <td className="px-3 py-3 font-mono text-[12px] font-medium text-neutral-700">{item.result_label}</td>
                <td className="py-3 pl-3 pr-3 text-[12px] text-neutral-500">{item.grade_label ?? "Pending"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
