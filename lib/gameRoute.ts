import { parseArchiveIndex } from "./archiveIndex";

/**
 * Which `/game/<id>` paths are not a published game (release 2.1.1, docs/plans/2.1.1.md item 1). The proxy rewrites them,
 * with status 404, to a server-rendered route, because in Next 16.4.6 a notFound() thrown while the game page renders sends
 * an empty shell and leaves the not-found content to JavaScript. The page keeps notFound() as the backstop for a listed id
 * whose file fails validation.
 */

/** The server-rendered not-found route. A static segment, so it wins over `[gamePk]`; requested directly it is also a 404. */
export const GAME_NOT_FOUND_PATH = "/game/unknown";

const ONE_GAME = /^\/game\/([^/]+)$/;

/** The ids of the published index, or null when it does not validate: then nothing is rewritten on a guess. */
export function publishedGameIds(index: unknown): ReadonlySet<string> | null {
  try {
    return new Set(parseArchiveIndex(index).games.map((row) => String(row.game_pk)));
  } catch {
    return null;
  }
}

/** Is this path one game id under `/game/` that is not in the published index? */
export function isUnpublishedGamePath(pathname: string, ids: ReadonlySet<string> | null): boolean {
  if (ids === null) return false;
  const match = ONE_GAME.exec(pathname);
  return match !== null && !ids.has(match[1]);
}
