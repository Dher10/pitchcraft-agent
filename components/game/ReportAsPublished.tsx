import StatTile from "@/components/StatTile";
import { InfoIcon } from "@/components/ui/Icons";
import { publishedDay, publishedReport, sideName, type Lineup } from "@/lib/archiveGame";
import { GAME_COPY } from "@/lib/copy/game";
import { formatDay } from "@/lib/format";
import type { ArchiveGameFile, ArchiveIndexRow } from "@/lib/types";

function LineupTiles({ name, lineup }: { name: string; lineup: Lineup }) {
  const caption = GAME_COPY.report.lineupCaption(lineup.vs_hand, lineup.scope);
  return (
    <div data-lineup className="rounded-md border border-line p-space-3">
      <h4 className="m-0 mb-space-2 text-title-md text-ink">{name}</h4>
      <dl className="m-0 grid grid-cols-3 gap-space-2">
        <StatTile label="OPS" value={lineup.ops} />
        <StatTile label="K%" value={lineup.k_rate} />
        <StatTile label="BB%" value={lineup.bb_rate} />
      </dl>
      {caption ? <p className="m-0 mt-space-2 text-caption text-ink-3">{caption}</p> : null}
    </div>
  );
}

/**
 * The report as it was published, in one block labelled by its origin: its own paragraphs, the lineups it described, the
 * questions it asked (with no answers and no promise of answers) and the critic's counts made before publishing. This is the
 * only place where text written before the game may appear; everything in it is the report's own.
 */
export default function ReportAsPublished({ game, row }: { game: ArchiveGameFile; row: ArchiveIndexRow | null }) {
  const report = publishedReport(game);
  const published = publishedDay(game);
  const label =
    game.origin.kind === "published_live" && published
      ? GAME_COPY.report.published(formatDay(published))
      : GAME_COPY.report.written(formatDay(game.origin.as_of));
  const paragraphs = report.sections.filter((section) => section.body !== undefined);
  const none = GAME_COPY.report.none;

  return (
    <section data-report-block className="grid gap-space-4 rounded-lg border border-line bg-surface p-space-4 bp-lg:p-space-5">
      <div>
        <h2 className="m-0 font-display text-title-lg text-ink">{GAME_COPY.report.title}</h2>
        <p className="m-0 mt-1 flex items-start gap-space-2 text-body-sm text-ink-2">
          <InfoIcon className="mt-0.5 size-4 flex-none" />
          {label}
        </p>
      </div>
      <div className="grid max-w-reading gap-space-3">
        {paragraphs.map((section, index) => (
          <div key={`${section.title}-${index}`}>
            <h3 className="m-0 text-title-md text-ink">{section.title}</h3>
            <p data-report-text className="m-0 mt-1 text-body-lg text-ink">{section.body}</p>
          </div>
        ))}
      </div>
      {report.lineups.away || report.lineups.home ? (
        <div className="grid gap-space-3 bp-md:grid-cols-2">
          {report.lineups.away ? <LineupTiles name={sideName(game, row, "away")} lineup={report.lineups.away} /> : null}
          {report.lineups.home ? <LineupTiles name={sideName(game, row, "home")} lineup={report.lineups.home} /> : null}
        </div>
      ) : null}
      {report.questions.length > 0 ? (
        <ul className="m-0 grid list-none gap-space-2 p-0">
          {report.questions.map((question) => (
            <li key={question} data-question className="text-body text-ink">
              <span className="text-ink-2">{GAME_COPY.report.weAsked}</span> <span data-report-text>{question}</span>
            </li>
          ))}
        </ul>
      ) : null}
      {report.critic ? (
        <p className="m-0 border-t border-line pt-space-3 text-body-sm text-ink-2">
          {GAME_COPY.report.critic(
            report.critic.checked,
            report.critic.unsupported === 0 ? none : String(report.critic.unsupported),
            report.critic.warnings === 0 ? none : String(report.critic.warnings),
          )}
        </p>
      ) : null}
    </section>
  );
}

