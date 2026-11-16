import type { ReactNode } from "react";
import { PlateIcon } from "@/components/ui/Icons";

/**
 * What a page shows when there is nothing to show: say what is missing in one plain sentence, say why if the data knows,
 * and offer one way forward. The symbol is the logo's plate, dashed. Never a spinner, a zero or internal error text.
 */
export default function EmptyState({
  title,
  children,
  action,
  heading = "h2",
}: {
  title: string;
  children?: ReactNode;
  action?: ReactNode;
  /** `h1` when the empty state is the whole page (a 404), `h2` inside a page that has its own title. */
  heading?: "h1" | "h2";
}) {
  const Heading = heading;
  return (
    <section className="flex flex-col items-center gap-space-3 rounded-lg border border-dashed border-line-strong px-space-4 py-space-6 text-center">
      <PlateIcon className="size-11 text-ink-3" />
      <Heading className="m-0 text-title-md text-ink">{title}</Heading>
      {children ? <p className="m-0 max-w-[42ch] text-ink-2">{children}</p> : null}
      {action}
    </section>
  );
}
