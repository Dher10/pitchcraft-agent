"use client";

import { useEffect, useId, useRef, useState } from "react";
import { HelpIcon } from "@/components/ui/Icons";
import { definitionOf, type GlossaryTerm } from "@/lib/glossary";
import { SITE_COPY } from "@/lib/copy/site";

/**
 * A term with its definition one tap away: a circled question mark after the label and a small panel that opens on tap,
 * on keyboard focus and on hover; Escape or a tap outside closes it. The text is the glossary's, word for word; a term
 * that is not in the glossary is refused (docs/design/COMPONENTS.md, Help).
 */
export default function Help({ term, align = "left" }: { term: GlossaryTerm; align?: "left" | "right" }) {
  const definition = definitionOf(term);
  const id = useId();
  const wrapper = useRef<HTMLSpanElement>(null);
  const pointerFocus = useRef(false);
  const [pinned, setPinned] = useState(false);
  const [hovered, setHovered] = useState(false);
  const [focused, setFocused] = useState(false);
  const open = pinned || hovered || focused;

  useEffect(() => {
    if (!open) return;
    const away = (event: Event) => {
      if (wrapper.current && !wrapper.current.contains(event.target as Node)) {
        setPinned(false);
        setHovered(false);
        setFocused(false);
      }
    };
    document.addEventListener("pointerdown", away);
    return () => document.removeEventListener("pointerdown", away);
  }, [open]);

  return (
    <span
      ref={wrapper}
      className="relative inline-flex items-center gap-1"
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      onKeyDown={(event) => {
        if (event.key === "Escape") {
          setPinned(false);
          setHovered(false);
          setFocused(false);
        }
      }}
    >
      <button
        type="button"
        aria-label={SITE_COPY.help.buttonName(term)}
        aria-expanded={open}
        aria-describedby={open ? id : undefined}
        onPointerDown={() => {
          pointerFocus.current = true;
        }}
        onFocus={() => {
          // A tap focuses the button and then clicks it: only a keyboard focus opens the panel by itself.
          if (!pointerFocus.current) setFocused(true);
        }}
        onBlur={() => {
          pointerFocus.current = false;
          setFocused(false);
        }}
        onClick={() => setPinned((value) => !value)}
        className="relative inline-flex size-[18px] flex-none cursor-help items-center justify-center rounded-full border-0 bg-transparent p-0 text-ink-3 after:absolute after:-inset-[13px] after:content-[''] hover:text-brand aria-expanded:text-brand"
      >
        <HelpIcon className="size-4" />
      </button>
      {open ? (
        <span
          id={id}
          role="tooltip"
          className={`absolute top-[calc(100%+8px)] z-10 w-[260px] max-w-[80vw] rounded-md bg-board p-space-3 text-left text-label font-normal tracking-normal whitespace-normal text-on-board shadow-pop ${
            align === "right" ? "right-0" : "left-0"
          }`}
        >
          <b className="block font-semibold text-signal">{term}</b>
          {definition}
        </span>
      ) : null}
    </span>
  );
}
