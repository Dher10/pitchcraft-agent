import ModeLine from "@/components/ModeLine";
import type { Metadata } from "@/lib/types";

interface HeroProps {
  metadata: Pick<Metadata, "data_mode" | "data_fetched_at">;
}

export default function Hero({ metadata }: HeroProps) {
  return (
    <section>
      <ModeLine dataMode={metadata.data_mode} fetchedAt={metadata.data_fetched_at} />
      <p className="mb-2 font-mono text-[10px] font-semibold uppercase tracking-[0.14em] text-neutral-400">
        Starter matchups, checked against the data
      </p>
      <h1 className="mb-1.5 text-[27px] font-bold leading-tight tracking-tight text-neutral-900">
        PitchCraft Matchup Agent
      </h1>
      <p className="max-w-xl text-sm leading-6 text-neutral-500">
        Each report reads the probable starters from public MLB data and says only what that data supports. No
        predictions, no betting.
      </p>
    </section>
  );
}
