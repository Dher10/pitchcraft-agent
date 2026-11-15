import Chip from "@/components/ui/Chip";
import { NOTABLE_COPY } from "@/lib/copy/notable";
import { ruleCount } from "@/lib/notableQuery";
import { NOTABLE_REASONS, reasonRule } from "@/lib/notableReasons";
import type { ArchiveIndex } from "@/lib/types";

/**
 * "How games are chosen": each rule in plain words with its count, from the same table the chips and pills use and from the
 * index's own tags, so the explanation and the list cannot disagree. It describes the rules, not the current list.
 */
export default function Rules({ index }: { index: ArchiveIndex }) {
  return (
    <aside aria-label={NOTABLE_COPY.rulesTitle} className="rounded-lg border border-line bg-surface p-space-4 bp-lg:p-space-5">
      <h2 className="m-0 font-display text-title-lg text-ink">{NOTABLE_COPY.rulesTitle}</h2>
      <p className="mt-2 mb-2 text-body-sm text-ink-2">{NOTABLE_COPY.rulesIntro(index.notable_count, index.count)}</p>
      <ul className="m-0 list-none p-0">
        {NOTABLE_REASONS.map((reason) => {
          const count = ruleCount(index, reason.key);
          return (
            <li key={reason.key} className="grid justify-items-start gap-1 border-t border-line py-2.5 first:border-t-0">
              <span className="flex w-full items-center justify-between gap-space-2">
                <Chip variant="reason">{reason.label}</Chip>
                <span className="text-body-sm text-ink-2">
                  <b className="tabular-nums text-ink">{count}</b>
                  {` ${NOTABLE_COPY.gamesWord(count)}`}
                </span>
              </span>
              <span className="text-body-sm text-ink-2">{reasonRule(reason.key, index.veteran_min)}</span>
            </li>
          );
        })}
      </ul>
    </aside>
  );
}
