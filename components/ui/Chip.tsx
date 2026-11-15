import type { ReactNode } from "react";
import { CheckIcon, CrossIcon, DashIcon, WarnIcon } from "@/components/ui/Icons";

export type ChipVariant = "neutral" | "ok" | "warn" | "bad" | "round" | "reason" | "feat" | "outline";

const BASE = "inline-flex min-h-6 items-center gap-space-1 rounded-sm px-2 py-0.5 text-label";

const STYLE: Record<ChipVariant, string> = {
  neutral: "bg-surface-sunken text-ink-2",
  ok: "bg-ok-tint text-ok",
  warn: "bg-warn-tint text-warn",
  bad: "bg-bad-tint text-bad",
  round: "bg-brand-tint text-brand",
  reason: "bg-signal-tint text-signal-ink",
  feat: "bg-signal font-semibold text-ink",
  outline: "border border-line-strong bg-transparent text-ink-2",
};

// A status is a word plus a shape, never color alone: ok has a check, warn a triangle, bad a cross.
const ICON: Partial<Record<ChipVariant, typeof CheckIcon>> = { ok: CheckIcon, warn: WarnIcon, bad: CrossIcon, neutral: undefined };

interface ChipProps {
  variant?: ChipVariant;
  /** A long phrase wraps; a chip is never truncated. */
  wrap?: boolean;
  /** A neutral chip that states "not present" or "not rated" may carry a dash. */
  dash?: boolean;
  children: ReactNode;
  className?: string;
  [data: `data-${string}`]: string | undefined;
}

/** A short fixed phrase with a meaning. Not a control. Every text is a catalog phrase, printed only when its rule is true. */
export default function Chip({ variant = "neutral", wrap = false, dash = false, children, className = "", ...data }: ChipProps) {
  const Icon = dash ? DashIcon : ICON[variant];
  return (
    <span {...data} className={`${BASE} ${STYLE[variant]} ${wrap ? "whitespace-normal" : "whitespace-nowrap"} ${className}`.trim()}>
      {Icon ? <Icon className="size-3 flex-none" /> : null}
      {children}
    </span>
  );
}
