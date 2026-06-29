import type { ArchiveItem, MatchupStatus } from "@/lib/types";

interface ArchiveTableProps {
  archive: ArchiveItem[];
}

const statusClasses: Record<MatchupStatus, string> = {
  upcoming: "bg-[#EEF3F8] text-[#1B3A5B]",
  final: "bg-[#EAF7EF] text-[#1E7A46]",
  demo: "bg-[#F2F4F7] text-[#475467]",
};

export default function ArchiveTable({ archive }: ArchiveTableProps) {
  return (
    <section className="rounded-lg border border-[#E5E8EC] bg-white p-5 sm:p-7">
      <div className="flex flex-col justify-between gap-2 sm:flex-row sm:items-end">
        <div>
          <p className="text-sm font-semibold uppercase tracking-[0.16em] text-[#1B3A5B]">
            Archive
          </p>
          <h2 className="mt-2 font-display text-2xl font-bold text-[#0F1722]">
            Last 7 Days
          </h2>
        </div>
      </div>
      <div className="mt-5 overflow-x-auto">
        <table className="w-full min-w-[760px] border-collapse text-left text-sm">
          <thead>
            <tr className="border-b border-[#E5E8EC] text-xs uppercase tracking-[0.12em] text-[#5B6573]">
              <th className="py-3 pr-4 font-bold">Date</th>
              <th className="px-4 py-3 font-bold">Matchup</th>
              <th className="px-4 py-3 font-bold">Status</th>
              <th className="px-4 py-3 font-bold">Starters</th>
              <th className="px-4 py-3 font-bold">Result</th>
              <th className="py-3 pl-4 font-bold">Grade</th>
            </tr>
          </thead>
          <tbody>
            {archive.map((item) => (
              <tr
                key={item.id}
                className="border-b border-[#E5E8EC] last:border-b-0"
              >
                <td className="tabular py-4 pr-4 font-medium text-[#0F1722]">
                  {item.date}
                </td>
                <td className="px-4 py-4 font-semibold text-[#0F1722]">
                  {item.title}
                  {item.featured ? (
                    <span className="ml-2 rounded-full bg-[#1B3A5B] px-2 py-0.5 text-[10px] font-bold uppercase tracking-[0.1em] text-white">
                      Featured
                    </span>
                  ) : null}
                </td>
                <td className="px-4 py-4">
                  <span
                    className={`rounded-full px-2.5 py-1 text-xs font-bold uppercase tracking-[0.1em] ${statusClasses[item.status]}`}
                  >
                    {item.status}
                  </span>
                </td>
                <td className="px-4 py-4 text-[#5B6573]">
                  {item.starter_summary}
                </td>
                <td className="px-4 py-4 text-[#5B6573]">
                  {item.result_label}
                </td>
                <td className="py-4 pl-4 font-medium text-[#0F1722]">
                  {item.grade_label ?? "Pending"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
