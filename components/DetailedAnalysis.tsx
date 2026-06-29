"use client";

import { useState } from "react";
import StrengthProfile from "@/components/StrengthProfile";
import ZoneDiagram, { getPitchColor } from "@/components/ZoneDiagram";
import type { Matchup, PitchLocationsByHand } from "@/lib/types";

type BatterHand = "vs_lhh" | "vs_rhh";
type StarterSide = "away_starter" | "home_starter";

interface DetailedAnalysisProps {
  matchup: Matchup;
}

export default function DetailedAnalysis({ matchup }: DetailedAnalysisProps) {
  return (
    <section className="space-y-4 rounded-xl border border-neutral-200 bg-white p-4">
      <h2 className="text-xl font-bold text-neutral-900">Detailed Analysis</h2>
      <PitcherAttack matchup={matchup} side="away_starter" locations={matchup.pitch_locations.away_starter} />
      <PitcherAttack matchup={matchup} side="home_starter" locations={matchup.pitch_locations.home_starter} />
      <StrengthProfile
        data={matchup.charts.strength_profile}
        awayStarterName={matchup.starters.away_starter.name}
        homeStarterName={matchup.starters.home_starter.name}
      />
    </section>
  );
}

function PitcherAttack({
  matchup,
  side,
  locations,
}: {
  matchup: Matchup;
  side: StarterSide;
  locations: PitchLocationsByHand;
}) {
  const [hand, setHand] = useState<BatterHand>("vs_lhh");
  const starter = matchup.starters[side];
  const velocityKey = side === "away_starter" ? "away_starter_velocity" : "home_starter_velocity";

  return (
    <article className="rounded-xl border border-neutral-200 bg-neutral-50 p-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <h3 className="font-bold text-neutral-900">How {starter.name} attacks</h3>
        <div className="flex w-fit rounded-lg border border-neutral-200 bg-white p-1">
          {(["vs_lhh", "vs_rhh"] as BatterHand[]).map((option) => (
            <button
              key={option}
              type="button"
              onClick={() => setHand(option)}
              className={`rounded-md px-3 py-1.5 text-xs font-bold uppercase ${
                hand === option ? "bg-blue-700 text-white" : "text-neutral-500"
              }`}
              title={option === "vs_lhh" ? "Versus left-handed hitters." : "Versus right-handed hitters."}
            >
              {option === "vs_lhh" ? "vs LHH" : "vs RHH"}
            </button>
          ))}
        </div>
      </div>
      <div className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-[1fr_auto]">
        <div className="space-y-3">
          {matchup.charts.pitch_mix.map((row) => {
            const usage = row[side][hand];
            return (
              <div key={`${side}-${row.pitch}`}>
                <div className="flex items-center justify-between text-sm">
                  <span className="font-medium text-neutral-800">{row.pitch}</span>
                  <span className="text-neutral-500" style={{ fontVariantNumeric: "tabular-nums" }}>{usage}%</span>
                </div>
                <div className="mt-1 h-2 rounded-full bg-neutral-200">
                  <div
                    className="h-2 rounded-full"
                    style={{ width: `${usage}%`, backgroundColor: getPitchColor(row.pitch) }}
                  />
                </div>
              </div>
            );
          })}
        </div>
        <div className="flex flex-col items-center">
          <ZoneDiagram locations={locations[hand]} width={160} height={190} />
          <p className="mt-2 text-center text-xs text-neutral-500">
            Target locations {hand === "vs_lhh" ? "against left-handed hitters" : "against right-handed hitters"}.
          </p>
        </div>
      </div>
      <div className="mt-4 flex flex-wrap gap-2">
        {matchup.charts.velocity_by_pitch.map((row) => {
          const value = row[velocityKey];
          return (
            <span key={`${side}-velo-${row.pitch}`} className="rounded-full bg-white px-3 py-1 text-xs text-neutral-600">
              {row.pitch}: {value === null ? "N/A" : `${value} mph`}
            </span>
          );
        })}
      </div>
    </article>
  );
}
