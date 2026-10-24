"use client";

import { useId, useState, type ButtonHTMLAttributes, type ReactNode } from "react";

export const STAT_TOOLTIPS: Record<string, string> = {
  LHH: "Left-handed hitters",
  RHH: "Right-handed hitters",
  ERA: "Earned run average: earned runs allowed per nine innings. Lower is better.",
  WHIP: "Walks plus hits per inning pitched. Lower is better.",
  K: "Strikeouts.",
  OPS: "On-base plus slugging: how often a lineup reaches base plus how much power it hits for. Higher means a stronger lineup.",
  "K%": "Share of plate appearances that end in a strikeout.",
  "BB%": "Share of plate appearances that end in a walk.",
  Break: "Total movement of the pitch, sideways and up or down, compared with a pitch thrown without spin.",
};

export default function Tooltip({ text, children, buttonProps }: {
  text: string;
  children: ReactNode;
  buttonProps?: ButtonHTMLAttributes<HTMLButtonElement>;
}) {
  const id = useId();
  const [focused, setFocused] = useState(false);
  const [hovered, setHovered] = useState(false);
  const [dismissed, setDismissed] = useState(false);
  const open = (focused || hovered) && !dismissed;
  const description = open ? id : undefined;
  return (
    <span className="relative inline-flex" onMouseEnter={() => { setHovered(true); setDismissed(false); }}
      onMouseLeave={() => setHovered(false)}
      onFocus={() => { setFocused(true); setDismissed(false); }} onBlur={() => setFocused(false)}
      onKeyDown={(event) => { if (event.key === "Escape") setDismissed(true); }}>
      {buttonProps ? (
        <button {...buttonProps} aria-describedby={description}>{children}</button>
      ) : (
        <span tabIndex={0} aria-describedby={description} className="cursor-help rounded-sm focus-visible:outline-2 focus-visible:outline-blue-700">
          {children}
        </span>
      )}
      {open ? <span id={id} role="tooltip"
        className="absolute bottom-full left-1/2 z-50 w-56 max-w-[80vw] -translate-x-1/2 rounded-md bg-neutral-900 p-2 text-left font-sans text-xs font-normal normal-case leading-5 tracking-normal text-white shadow-lg">
        {text}
      </span> : null}
    </span>
  );
}
