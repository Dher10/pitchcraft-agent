"use client";

import { useState } from "react";
import PitchTrajectoryCard from "@/components/PitchTrajectoryCard";
import StrengthProfile from "@/components/StrengthProfile";
import TeamBadge from "@/components/TeamBadge";
import ZoneDiagram, { getPitchColor } from "@/components/ZoneDiagram";
import { describePitchMovement } from "@/lib/pitchDescriptions";
import type { Matchup, PitchFamily, PitchLocationsByHand } from "@/lib/types";

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
  const [selectedPitch, setSelectedPitch] = useState(() => matchup.charts.pitch_mix[0]?.pitch ?? "Four-seam");
  const starter = matchup.starters[side];
  const velocityKey = side === "away_starter" ? "away_starter_velocity" : "home_starter_velocity";
  const selectedRow = matchup.charts.pitch_mix.find((row) => row.pitch === selectedPitch) ?? matchup.charts.pitch_mix[0];
  const selectedVelocityRow = matchup.charts.velocity_by_pitch.find((row) => row.pitch === selectedRow?.pitch);
  const selectedVelocity = selectedVelocityRow?.[velocityKey] ?? "N/A";
  const selectedMovement = matchup.charts.pitch_movement?.[side]?.[selectedRow?.pitch ?? ""];
  const family = selectedMovement?.family ?? inferPitchFamily(selectedRow?.pitch ?? "");
  const hBreak = selectedMovement?.h_break ?? 0;
  const vBreak = selectedMovement?.v_break ?? 0;
  const usage = selectedRow?.[side][hand] ?? 0;
  const throwsHand = normalizeThrows(starter.throws);

  return (
    <article className="rounded-xl border border-neutral-200 bg-neutral-50 p-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-2.5">
          <TeamBadge abbreviation={starter.team} size={22} />
          <h3 className="font-bold text-neutral-900">How {starter.name} attacks</h3>
        </div>
        <div className="flex w-fit rounded-lg border border-neutral-200 bg-white p-1">
          {(["vs_lhh", "vs_rhh"] as BatterHand[]).map((option) => (
            <button
              key={option}
              type="button"
              onClick={() => setHand(option)}
              className={`rounded-md px-3 py-1.5 font-mono text-[10px] font-bold uppercase tracking-wide ${
                hand === option ? "bg-blue-700 text-white" : "text-neutral-500"
              }`}
              title={option === "vs_lhh" ? "Versus left-handed hitters." : "Versus right-handed hitters."}
            >
              {option === "vs_lhh" ? "vs LHH" : "vs RHH"}
            </button>
          ))}
        </div>
      </div>
      <div className="mt-4 grid grid-cols-1 gap-4 xl:grid-cols-[minmax(0,1fr)_minmax(260px,0.85fr)_auto]">
        <div className="space-y-2">
          {matchup.charts.pitch_mix.map((row) => {
            const rowUsage = row[side][hand];
            const isSelected = row.pitch === selectedRow?.pitch;
            return (
              <button
                key={`${side}-${row.pitch}`}
                type="button"
                aria-pressed={isSelected}
                onClick={() => setSelectedPitch(row.pitch)}
                onFocus={() => setSelectedPitch(row.pitch)}
                onMouseEnter={() => setSelectedPitch(row.pitch)}
                className={`w-full rounded-lg border p-2.5 text-left transition ${
                  isSelected ? "border-blue-200 bg-blue-50" : "border-neutral-100 bg-white hover:border-neutral-200"
                }`}
              >
                <span className="flex items-center gap-1.5 text-[11px] font-semibold leading-4 text-neutral-700">
                  <span className="h-2 w-2 shrink-0 rounded-full" style={{ backgroundColor: getPitchColor(row.pitch) }} />
                  <span>{row.pitch}</span>
                </span>
                <span
                  className="mt-1.5 block font-mono text-sm font-semibold text-neutral-900"
                  style={{ fontVariantNumeric: "tabular-nums" }}
                >
                  {rowUsage}%
                </span>
                <span className="mt-1.5 block h-[5px] rounded-full bg-neutral-200">
                  <span
                    className="block h-[5px] rounded-full"
                    style={{ width: `${rowUsage}%`, backgroundColor: getPitchColor(row.pitch) }}
                  />
                </span>
              </button>
            );
          })}
        </div>
        {selectedRow ? (
          <PitchTrajectoryCard
            pitchName={selectedRow.pitch}
            family={family}
            velocity={selectedVelocity ?? "N/A"}
            usagePct={usage}
            hBreak={hBreak}
            vBreak={vBreak}
            throwsHand={throwsHand}
            team={starter.team}
            description={describePitchMovement({ family, velocity: selectedVelocity ?? "N/A", hBreak, vBreak })}
          />
        ) : null}
        <div className="flex flex-col items-center">
          <ZoneDiagram locations={locations[hand]} width={205} height={244} />
          <p className="mt-2 max-w-[220px] text-center text-xs text-neutral-500">
            Target locations {hand === "vs_lhh" ? "against left-handed hitters" : "against right-handed hitters"}.
          </p>
        </div>
      </div>
      {starter.sample ? (
        <p className="mt-3 font-mono text-[10px] text-neutral-400">
          {starter.sample.limited.arsenal
            ? `Arsenal data limited: ${starter.sample.arsenal.pitches ?? 0} pitches (${starter.sample.thresholds.arsenal} needed)`
            : `Pitch data: ${starter.sample.arsenal.scope.label}`}
        </p>
      ) : null}
      <div className="mt-4 border-t border-neutral-200 pt-3 font-mono text-[10px] text-neutral-400">
        {matchup.charts.velocity_by_pitch
          .map((row) => {
            const value = row[velocityKey];
            return `${row.pitch} ${value === null ? "N/A" : `${value} mph`}`;
          })
          .join("  ·  ")}
      </div>
    </article>
  );
}

function normalizeThrows(raw: string): "L" | "R" {
  return raw?.toUpperCase().startsWith("L") ? "L" : "R";
}

function inferPitchFamily(pitch: string): PitchFamily {
  const value = pitch.toLowerCase();
  if (value.includes("slider") || value.includes("curve") || value.includes("sweeper") || value.includes("slurve")) {
    return "Breaking";
  }
  if (value.includes("change") || value.includes("split") || value.includes("fork") || value.includes("knuckle")) {
    return "Offspeed";
  }
  return "Fastball";
}
