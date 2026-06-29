import type { Report } from "@/lib/types";

interface ScoutingReportProps {
  report: Report;
}

export default function ScoutingReport({ report }: ScoutingReportProps) {
  return (
    <section className="rounded-lg border border-[#E5E8EC] bg-white p-5 sm:p-7">
      <p className="text-sm font-semibold uppercase tracking-[0.16em] text-[#1B3A5B]">
        Scouting Report
      </p>
      <h2 className="mt-3 font-display text-3xl font-black leading-tight text-[#0F1722]">
        {report.headline}
      </h2>
      <ul className="mt-6 grid gap-3 md:grid-cols-3">
        {report.short_summary.map((item) => (
          <li
            key={item}
            className="rounded-md border border-[#E5E8EC] bg-[#F7F8FA] p-4 text-sm leading-6 text-[#0F1722]"
          >
            {item}
          </li>
        ))}
      </ul>

      <div className="mt-7 grid gap-5">
        {report.sections.map((section) => (
          <article key={section.title} className="border-t border-[#E5E8EC] pt-5">
            <h3 className="font-display text-xl font-bold text-[#0F1722]">
              {section.title}
            </h3>
            {section.body ? (
              <p className="mt-2 max-w-4xl text-base leading-8 text-[#5B6573]">
                {section.body}
              </p>
            ) : null}
            {section.bullets ? (
              <ul className="mt-3 grid gap-2 text-base leading-7 text-[#5B6573]">
                {section.bullets.map((bullet) => (
                  <li key={bullet} className="flex gap-3">
                    <span className="mt-3 h-1.5 w-1.5 shrink-0 rounded-full bg-[#1B3A5B]" />
                    <span>{bullet}</span>
                  </li>
                ))}
              </ul>
            ) : null}
          </article>
        ))}
      </div>
    </section>
  );
}
