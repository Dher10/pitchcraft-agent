import type { ReactNode } from "react";
import { InfoIcon, WarnIcon, CrossIcon } from "@/components/ui/Icons";

export type NoticeTone = "neutral" | "warn" | "bad";

const STYLE: Record<NoticeTone, string> = {
  neutral: "bg-surface-sunken text-ink",
  warn: "bg-warn-tint text-warn",
  bad: "bg-bad-tint text-bad",
};
const ICON = { neutral: InfoIcon, warn: WarnIcon, bad: CrossIcon } as const;

/**
 * Less than usual to show, in one plain sentence and in a status region: the index is missing, a probable starter did not
 * start, a sample is small. The tone is carried by its icon and its words as well as by its color.
 */
export default function Notice({ tone = "neutral", children }: { tone?: NoticeTone; children: ReactNode }) {
  const Icon = ICON[tone];
  return (
    <div role="status" className={`flex items-start gap-space-3 rounded-md px-space-4 py-space-3 text-body-sm ${STYLE[tone]}`}>
      <Icon className="mt-px size-[18px] flex-none" />
      <p className="m-0 text-ink">{children}</p>
    </div>
  );
}
