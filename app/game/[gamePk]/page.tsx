import type { Metadata } from "next";
import { notFound } from "next/navigation";
import GameView from "@/components/game/GameView";
import { gameMetadata, loadArchiveGame, matchingRow, seriesNeighbors } from "@/lib/archiveGame";
import { getArchiveIndex } from "@/lib/data";

interface GamePageProps {
  params: Promise<{ gamePk: string }>;
}

export async function generateMetadata({ params }: GamePageProps): Promise<Metadata> {
  const game = await loadArchiveGame((await params).gamePk);
  if (game === null) return {};
  return gameMetadata(game, matchingRow(game, await getArchiveIndex()));
}

export default async function GamePage({ params }: GamePageProps) {
  const [game, index] = await Promise.all([loadArchiveGame((await params).gamePk), getArchiveIndex()]);
  // An invalid id, an unknown game and a file that is not valid are all a 404, never a blank page (R4 5.2).
  if (game === null) notFound();
  const row = matchingRow(game, index);
  const { previous, next } = row && index ? seriesNeighbors(index, game.game_pk) : { previous: null, next: null };
  return <GameView game={game} row={row} previous={previous} next={next} />;
}
