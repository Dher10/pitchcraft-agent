import FinalLine from "@/components/ui/FinalLine";
import Help from "@/components/ui/Help";
import { SITE_COPY } from "@/lib/copy/site";
import Notice from "@/components/ui/Notice";
import TeamBadge from "@/components/TeamBadge";
import { clubAbbreviation, reportStarter, sideName } from "@/lib/archiveGame";
import { GAME_COPY } from "@/lib/copy/game";
import { getTeamColor } from "@/lib/teamColors";
import type { ArchiveGameFile, ArchiveIndexRow } from "@/lib/types";

/**
 * One starter after the game, from the envelope: the club and role, his name, the hand and style the report gave him (only
 * when the probable starter is the one who started), his final line from the box score, and a note when the probable starter
 * did not start or the box score could not say. No pitches, no Game Score and no summary sentence: the 1.0.0 file has none.
 */
export default function StarterResult({ game, row, side }: { game: ArchiveGameFile; row: ArchiveIndexRow | null; side: "away" | "home" }) {
  const check = game.starters_check[side];
  const actual = game.starters_check.actual[side];
  const probable = reportStarter(game, side);
  const club = sideName(game, row, side);
  const abbreviation = clubAbbreviation(game, row, side);
  const role = side === "away" ? GAME_COPY.roleAway(club) : GAME_COPY.roleHome(club);
  // The report's hand and style describe the probable starter, so they are shown only when he is the one who started.
  const profile =
    check === "started" ? GAME_COPY.handAndStyle(probable.hand ? GAME_COPY.hand[probable.hand] : null, probable.style) : "";

  return (
    <article
      data-starter={side}
      style={{ borderTopColor: getTeamColor(abbreviation).bg }}
      className="grid content-start gap-space-4 rounded-lg border border-t-4 border-line bg-surface p-space-4 bp-lg:p-space-5"
    >
      <div className="flex items-start justify-between gap-space-3">
        <div>
          <div className="text-label text-ink-2">{role}</div>
          {actual ? <h3 className="my-1 font-display text-title-lg text-ink">{actual.name}</h3> : null}
          {profile ? <div className="text-body-sm text-ink-2">{profile}</div> : null}
        </div>
        <TeamBadge abbreviation={abbreviation} size={48} />
      </div>
      {check === "did_not_start" && actual && probable.name ? (
        <Notice tone="warn">{GAME_COPY.probableDidNotStart(probable.name, actual.name)}</Notice>
      ) : null}
      {check === "unknown" ? <Notice>{GAME_COPY.starterNotConfirmed}</Notice> : null}
      <div className="grid gap-space-2">
        {game.final_line[side] ? (
          <div className="flex items-center gap-1 text-label text-ink-2">
            {SITE_COPY.finalLine.label}
            <Help term="Final line" />
          </div>
        ) : null}
        <FinalLine line={game.final_line[side]} />
      </div>
    </article>
  );
}
