import Link from "next/link";
import type { ButtonHTMLAttributes, ReactNode } from "react";

export type ButtonVariant = "primary" | "signal" | "secondary" | "quiet";

const BASE =
  "inline-flex min-h-tap items-center justify-center gap-space-2 rounded-sm border px-space-4 text-body font-semibold no-underline cursor-pointer";

const STYLE: Record<ButtonVariant, string> = {
  primary: "border-brand bg-brand text-on-brand hover:border-brand-strong hover:bg-brand-strong hover:text-on-brand",
  signal: "border-signal bg-signal text-ink hover:border-signal-tint hover:bg-signal-tint hover:text-ink",
  secondary: "border-line-strong bg-surface text-ink hover:border-ink-2 hover:bg-surface-sunken hover:text-ink",
  quiet: "border-transparent bg-transparent px-space-2 text-brand underline underline-offset-4 hover:bg-brand-tint hover:text-brand",
};

type ButtonProps =
  | ({ href: string; variant?: ButtonVariant; children: ReactNode } & { type?: never })
  | ({ href?: undefined; variant?: ButtonVariant; children: ReactNode } & ButtonHTMLAttributes<HTMLButtonElement>);

/**
 * Navigation is a link and only a form submit is a button (docs/design/COMPONENTS.md, Button). One primary per view; the
 * label says what happens, in the page's words. 44 px tall.
 */
export default function Button(props: ButtonProps) {
  const variant = props.variant ?? "primary";
  const className = `${BASE} ${STYLE[variant]}`;
  if (props.href !== undefined) {
    return (
      <Link href={props.href} prefetch={false} className={className}>
        {props.children}
      </Link>
    );
  }
  const { variant: _variant, children, ...rest } = props;
  void _variant;
  return (
    <button {...rest} className={className}>
      {children}
    </button>
  );
}
