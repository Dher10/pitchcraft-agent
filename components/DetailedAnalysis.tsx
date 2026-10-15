"use client";

import { useState } from "react";
import PitchTrajectoryCard from "@/components/PitchTrajectoryCard";
import StrengthProfile from "@/components/StrengthProfile";
import TeamBadge from "@/components/TeamBadge";
import ZoneDiagram, { getPitchColor } from "@/components/ZoneDiagram";
import { describePitchMovement } from "@/lib/pitchDescriptions";
import type { Matchup, PitchFamily, PitchLocationsByHand, PitchUsage } from "@/lib/types";

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
  const [selectedPitch, setSelectedPitch] = useState<string | null>(null);
  const starter = matchup.starters[side];
  const velocityKey = side === "away_starter" ? "away_starter_velocity" : "home_starter_velocity";
  // The combined chart lists the pitches of both starters; this panel shows only his own.
  const arsenal = matchup.charts.pitch_mix.filter((row) => wasThrown(row[side]));
  const arsenalLimited = Boolean(starter.sample?.limited.arsenal);
  const selectedRow = arsenal.find((row) => row.pitch === selectedPitch) ?? arsenal[0];
  const velocityOf = (pitch: string) =>
    matchup.charts.velocity_by_pitch.find((row) => row.pitch === pitch)?.[velocityKey] ?? null;
  const selectedVelocity = selectedRow ? velocityOf(selectedRow.pitch) : null;
  const selectedMovement = selectedRow ? matchup.charts.pitch_movement?.[side]?.[selectedRow.pitch] : undefined;
  const family = selectedMovement?.family ?? inferPitchFamily(selectedRow?.pitch ?? "");
  // Unavailable movement stays null; it is never drawn or described as a measured 0.0.
  const hBreak = selectedMovement?.h_break ?? null;
  const vBreak = selectedMovement?.v_break ?? null;
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
      {selectedRow ? (
        <div className="mt-4 grid grid-cols-1 gap-4 xl:grid-cols-[minmax(0,1fr)_minmax(260px,0.85fr)_auto]">
          <div className="space-y-2">
            {arsenal.map((row) => {
              const rowUsage = row[side][hand];
              const isSelected = row.pitch === selectedRow.pitch;
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
                    {rowUsage === null ? "—" : `${rowUsage}%`}
                  </span>
                  {rowUsage === null ? null : (
                    <span className="mt-1.5 block h-[5px] rounded-full bg-neutral-200">
                      <span
                        className="block h-[5px] rounded-full"
                        style={{ width: `${rowUsage}%`, backgroundColor: getPitchColor(row.pitch) }}
                      />
                    </span>
                  )}
                </button>
              );
            })}
            {arsenal.every((row) => row[side][hand] === null) ? (
              <p className="text-xs text-neutral-500">
                No {hand === "vs_lhh" ? "left-handed" : "right-handed"} batters faced.
              </p>
            ) : null}
          </div>
          {arsenalLimited ? (
            <p className="rounded-lg border border-neutral-200 bg-white p-4 text-sm leading-6 text-neutral-600">
              The arsenal sample is too small, so pitch shapes are not described for {starter.name}.
            </p>
          ) : hBreak !== null && vBreak !== null ? (
            <PitchTrajectoryCard
              pitchName={selectedRow.pitch}
              family={family}
              velocity={selectedVelocity ?? "N/A"}
              usagePct={selectedRow[side][hand]}
              hBreak={hBreak}
              vBreak={vBreak}
              throwsHand={throwsHand}
              team={starter.team}
              description={describePitchMovement({ family, velocity: selectedVelocity ?? "N/A", hBreak, vBreak })}
            />
          ) : (
            <aside className="rounded-lg border border-neutral-200 bg-white p-4">
              <h4 className="text-base font-bold text-neutral-900">{selectedRow.pitch}</h4>
              <p className="mt-1 font-mono text-[10.5px] text-neutral-400">
                {throwsHand ? `${throwsHand}HP · ` : ""}
                {selectedVelocity === null ? "N/A" : `${selectedVelocity} mph`}
              </p>
              <p className="mt-3 text-sm leading-6 text-neutral-600">Movement data not available for this pitch.</p>
            </aside>
          )}
          <div className="flex flex-col items-center">
            <ZoneDiagram locations={locations[hand]} width={205} height={244} />
            <p className="mt-2 max-w-[220px] text-center text-xs text-neutral-500">
              Target locations {hand === "vs_lhh" ? "against left-handed hitters" : "against right-handed hitters"}.
            </p>
          </div>
        </div>
      ) : (
        <p className="mt-4 rounded-lg border border-neutral-200 bg-white p-4 text-sm leading-6 text-neutral-600">
          {starter.name} has no pitches on record, so there is no arsenal to show.
        </p>
      )}
      {starter.sample ? (
        <p className="mt-3 font-mono text-[10px] text-neutral-400">
          {starter.sample.limited.arsenal
            ? `Arsenal data limited: ${
                starter.sample.arsenal.pitches === null || starter.sample.arsenal.pitches === undefined
                  ? "pitch count not available"
                  : `${starter.sample.arsenal.pitches} pitches`
              } (${starter.sample.thresholds.arsenal} needed)`
            : starter.sample.arsenal.scope
              ? `Pitch data: ${starter.sample.arsenal.scope.label}`
              : null}
        </p>
      ) : null}
      {arsenal.length > 0 ? (
        <div className="mt-4 border-t border-neutral-200 pt-3 font-mono text-[10px] text-neutral-400">
          {arsenal
            .map((row) => {
              const value = velocityOf(row.pitch);
              return `${row.pitch} ${value === null ? "N/A" : `${value} mph`}`;
            })
            .join("  ·  ")}
        </div>
      ) : null}
    </article>
  );
}

/** Only a hand the data gives is shown: anything else (a switch pitcher, a missing value) prints no hand. */
function normalizeThrows(raw: string | null | undefined): "L" | "R" | null {
  const hand = raw?.toUpperCase().charAt(0);
  return hand === "L" || hand === "R" ? hand : null;
}

/**
 * Whether a starter threw this pitch. The raw count decides when the data has it: a pitch thrown once
 * in 3,000 has a share that rounds to 0.0 and was still thrown.
 */
function wasThrown(usage: PitchUsage): boolean {
  return typeof usage.count === "number" ? usage.count > 0 : usage.overall > 0;
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
