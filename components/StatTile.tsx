import Tooltip, { STAT_TOOLTIPS } from "@/components/Tooltip";

interface StatTileProps {
  label: string;
  title?: string;
  value: string | number;
  align?: "left" | "center";
}

export default function StatTile({ label, title, value, align = "left" }: StatTileProps) {
  return (
    <div
      className={`rounded-lg border border-neutral-100 bg-neutral-50 px-2.5 py-2 ${
        align === "center" ? "text-center" : ""
      }`}
    >
      <dt className="font-mono text-[9px] font-semibold uppercase tracking-widest text-neutral-400">
        {STAT_TOOLTIPS[label] ? <Tooltip text={STAT_TOOLTIPS[label]}>{label}</Tooltip> : (
          <span title={title} className="cursor-help">{label}</span>
        )}
      </dt>
      <dd className="mt-1 font-mono text-base font-semibold text-neutral-900" style={{ fontVariantNumeric: "tabular-nums" }}>
        {value}
      </dd>
    </div>
  );
}
