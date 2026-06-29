import ArchiveTable from "@/components/ArchiveTable";
import CriticReviewPanel from "@/components/CriticReviewPanel";
import Disclaimer from "@/components/Disclaimer";
import FeaturedMatchupCard from "@/components/FeaturedMatchupCard";
import Hero from "@/components/Hero";
import MatchupSummary from "@/components/MatchupSummary";
import PitchMixChart from "@/components/PitchMixChart";
import ScoutingReport from "@/components/ScoutingReport";
import StarterCard from "@/components/StarterCard";
import StrengthProfile from "@/components/StrengthProfile";
import VelocityChart from "@/components/VelocityChart";
import { getPitchCraftData } from "@/lib/data";
import type { CallResult, Matchup, StarterLine } from "@/lib/types";

const callResultClasses: Record<CallResult, string> = {
  held_up: "bg-[#EAF7EF] text-[#1E7A46]",
  partially_held_up: "bg-[#FFF5D6] text-[#9A6B00]",
  did_not_hold_up: "bg-[#FDEDEC] text-[#B42318]",
  unclear: "bg-[#F2F4F7] text-[#475467]",
};

export default async function Home() {
  const data = await getPitchCraftData();
  const featuredMatchup = data.matchups.find(
    (matchup) => matchup.id === data.featured_matchup_id
  );

  if (!featuredMatchup) {
    throw new Error(`Featured matchup not found: ${data.featured_matchup_id}`);
  }

  return (
    <div className="min-h-screen bg-[#F7F8FA] text-[#0F1722]">
      <Hero metadata={data.metadata} workflow={data.agent_workflow} />

      <main className="mx-auto flex w-full max-w-6xl flex-col gap-6 px-5 pb-12 sm:px-8 lg:px-10">
        <FeaturedMatchupCard
          date={featuredMatchup.date}
          status={featuredMatchup.status}
          game={featuredMatchup.game}
          teams={featuredMatchup.teams}
          starters={featuredMatchup.starters}
          report={featuredMatchup.report}
          dataConfidence={featuredMatchup.data_confidence}
        />

        <MatchupSummary
          game={featuredMatchup.game}
          teams={featuredMatchup.teams}
        />

        <section className="grid gap-4 lg:grid-cols-2">
          <StarterCard starter={featuredMatchup.starters.away_starter} />
          <StarterCard starter={featuredMatchup.starters.home_starter} />
        </section>

        <section className="grid gap-4 xl:grid-cols-3">
          <PitchMixChart
            data={featuredMatchup.charts.pitch_mix}
            awayStarterName={featuredMatchup.starters.away_starter.name}
            homeStarterName={featuredMatchup.starters.home_starter.name}
          />
          <VelocityChart
            data={featuredMatchup.charts.velocity_by_pitch}
            awayStarterName={featuredMatchup.starters.away_starter.name}
            homeStarterName={featuredMatchup.starters.home_starter.name}
          />
          <StrengthProfile
            data={featuredMatchup.charts.strength_profile}
            awayStarterName={featuredMatchup.starters.away_starter.name}
            homeStarterName={featuredMatchup.starters.home_starter.name}
          />
        </section>

        <ScoutingReport report={featuredMatchup.report} />
        <CriticReviewPanel review={featuredMatchup.critic_review} />
        <PostgameSlot matchup={featuredMatchup} />
        <ArchiveTable archive={data.archive} />
      </main>

      <Disclaimer disclaimers={data.disclaimers} />
    </div>
  );
}

function PostgameSlot({ matchup }: { matchup: Matchup }) {
  if (!matchup.postgame) {
    return (
      <section className="rounded-lg border border-[#E5E8EC] bg-white p-5 text-sm text-[#5B6573]">
        Postgame review appears here after the game.
      </section>
    );
  }

  const { postgame } = matchup;
  const awayLine = postgame.starter_lines.away_starter;
  const homeLine = postgame.starter_lines.home_starter;

  return (
    <section className="rounded-lg border border-[#E5E8EC] bg-white p-5 sm:p-7">
      <div className="flex flex-col justify-between gap-4 md:flex-row md:items-end">
        <div>
          <p className="text-sm font-semibold uppercase tracking-[0.16em] text-[#1B3A5B]">
            Postgame Review
          </p>
          <h2 className="mt-3 font-display text-3xl font-black text-[#0F1722]">
            {matchup.teams.away.abbreviation}{" "}
            <span className="tabular">
              {postgame.final_score.away_team_runs}
            </span>
            {" - "}
            {matchup.teams.home.abbreviation}{" "}
            <span className="tabular">
              {postgame.final_score.home_team_runs}
            </span>
          </h2>
        </div>
        <p className="rounded-full bg-[#EAF7EF] px-3 py-1.5 text-sm font-bold text-[#1E7A46]">
          Starter duel: {postgame.starter_duel_winner}
        </p>
      </div>

      <div className="mt-6 grid gap-4 lg:grid-cols-2">
        <StarterGrade line={awayLine} />
        <StarterGrade line={homeLine} />
      </div>

      <div className="mt-6">
        <h3 className="font-display text-xl font-bold text-[#0F1722]">
          Call Check
        </h3>
        <div className="mt-3 grid gap-3">
          {postgame.call_check.map((check) => (
            <article
              key={`${check.pregame_note}-${check.result}`}
              className="rounded-lg border border-[#E5E8EC] bg-[#F7F8FA] p-4"
            >
              <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                <p className="font-semibold leading-6 text-[#0F1722]">
                  {check.pregame_note}
                </p>
                <span
                  className={`w-fit rounded-full px-3 py-1 text-xs font-bold uppercase tracking-[0.1em] ${callResultClasses[check.result]}`}
                >
                  {check.result.replaceAll("_", " ")}
                </span>
              </div>
              <p className="mt-2 text-sm leading-6 text-[#5B6573]">
                {check.postgame_evidence}
              </p>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}

function StarterGrade({ line }: { line: StarterLine }) {
  return (
    <article className="rounded-lg border border-[#E5E8EC] bg-[#F7F8FA] p-4">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h3 className="font-display text-2xl font-bold text-[#0F1722]">
            {line.name}
          </h3>
          <p className="tabular mt-1 text-sm text-[#5B6573]">
            {line.innings_pitched} IP, {line.earned_runs} ER, {line.strikeouts}{" "}
            K, {line.walks} BB, {line.home_runs_allowed} HR
          </p>
        </div>
        <span className="tabular font-display text-3xl font-black text-[#1B3A5B]">
          {line.pitchcraft_grade}
        </span>
      </div>
      <p className="mt-3 text-sm leading-6 text-[#5B6573]">
        {line.grade_explanation}
      </p>
    </article>
  );
}
