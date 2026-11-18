import type { Metadata } from "next";
import GameNotFound from "@/components/game/GameNotFound";

// The proxy rewrites an unknown or malformed /game/<id> here with status 404 (lib/gameRoute.ts), so the heading and the
// links are in the server's HTML and work without JavaScript.
export const metadata: Metadata = { robots: { index: false, follow: true } };

export default function UnknownGamePage() {
  return <GameNotFound />;
}
