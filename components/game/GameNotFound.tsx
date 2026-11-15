import Button from "@/components/ui/Button";
import EmptyState from "@/components/ui/EmptyState";
import { GAME_COPY } from "@/lib/copy/game";

/** An unknown, invalid or unreadable game: the empty state with the ways back, never a blank page or an error text. */
export default function GameNotFound() {
  return (
    <main className="mx-auto max-w-[1184px] px-space-4 py-space-7 bp-lg:px-space-6">
      <EmptyState
        title={GAME_COPY.notFound.title}
        action={
          <div className="flex flex-wrap justify-center gap-space-3">
            <Button href="/archive" variant="secondary">{GAME_COPY.notFound.archive}</Button>
            <Button href="/notable" variant="secondary">{GAME_COPY.notFound.notable}</Button>
          </div>
        }
      />
    </main>
  );
}
