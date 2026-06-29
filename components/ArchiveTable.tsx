import type { ArchiveItem, MatchupStatus } from "@/lib/types";

interface ArchiveTableProps {
  archive: ArchiveItem[];
}

const statusClasses: Record<MatchupStatus, string> = {
  upcoming: "bg-neutral-100 text-neutral-600",
  final: "bg-green-100 text-green-800",
  demo: "bg-neutral-100 text-neutral-600",
};

export default function ArchiveTable({ archive }: ArchiveTableProps) {
  return (
    <section className="rounded-xl border border-neutral-200 bg-white p-4">
      <h2 className="text-xl font-bold text-neutral-900">Archive</h2>
      <div className="mt-4 overflow-x-auto">
        <table className="w-full min-w-[720px] border-collapse text-left text-sm">
          <thead>
            <tr className="border-b border-neutral-200 text-xs uppercase tracking-wide text-neutral-500">
              <th className="py-3 pr-3 font-bold">Date</th>
              <th className="px-3 py-3 font-bold">Matchup</th>
              <th className="px-3 py-3 font-bold">Status</th>
              <th className="px-3 py-3 font-bold">Starters</th>
              <th className="px-3 py-3 font-bold">Result</th>
              <th className="py-3 pl-3 font-bold">Grade</th>
            </tr>
          </thead>
          <tbody>
            {archive.map((item) => (
              <tr key={item.id} className="border-b border-neutral-200 last:border-b-0">
                <td className="py-3 pr-3 font-medium text-neutral-900" style={{ fontVariantNumeric: "tabular-nums" }}>
                  {item.date}
                </td>
                <td className="px-3 py-3 font-semibold text-neutral-900">
                  {item.title}
                  {item.featured ? (
                    <span className="ml-2 rounded-full bg-blue-100 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide text-blue-700">
                      Featured
                    </span>
                  ) : null}
                </td>
                <td className="px-3 py-3">
                  <span className={`rounded-full px-2.5 py-1 text-[11px] font-bold uppercase tracking-wide ${statusClasses[item.status]}`}>
                    {item.status}
                  </span>
                </td>
                <td className="px-3 py-3 text-neutral-600">{item.starter_summary}</td>
                <td className="px-3 py-3 text-neutral-600">{item.result_label}</td>
                <td className="py-3 pl-3 font-medium text-neutral-900">{item.grade_label ?? "Pending"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
