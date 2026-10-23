"use client";

import { useState } from "react";
import AgentPipeline from "@/components/AgentPipeline";
import ArchiveTable from "@/components/ArchiveTable";
import Disclaimer from "@/components/Disclaimer";
import GameCarousel from "@/components/GameCarousel";
import Hero from "@/components/Hero";
import MatchupView from "@/components/MatchupView";
import type { PitchCraftData } from "@/lib/types";

interface PitchCraftAppProps {
  data: PitchCraftData;
  initialSelectedId?: string;
}

export default function PitchCraftApp({ data, initialSelectedId }: PitchCraftAppProps) {
  const [selectedId, setSelectedId] = useState(initialSelectedId ?? data.featured_matchup_id);
  // A day with no games has no matchup (schema 0.9.0): the page keeps the rest and draws no game.
  const selected =
    data.matchups.find((matchup) => matchup.id === selectedId) ??
    data.matchups.find((matchup) => matchup.id === data.featured_matchup_id) ??
    data.matchups[0];

  return (
    <main className="mx-auto flex max-w-3xl flex-col gap-7 px-4 py-10">
      <Hero metadata={data.metadata} />
      {selected ? (
        <>
          <GameCarousel
            matchups={data.matchups}
            archive={data.archive}
            featuredId={data.featured_matchup_id}
            selectedId={selected.id}
            onSelect={setSelectedId}
          />
          <MatchupView matchup={selected} />
        </>
      ) : null}
      <AgentPipeline workflow={data.agent_workflow} />
      {data.metadata.data_mode === "fetched_snapshot" && data.matchups.length === 0 &&
      data.metadata.data_status?.live_run?.status === "no_games" ? (
        <p className="text-sm text-neutral-600" role="status">
          No MLB games scheduled on {data.metadata.data_status.live_run.target_date}.
        </p>
      ) : null}
      <ArchiveTable archive={data.archive} />
      <Disclaimer disclaimers={data.disclaimers} />
    </main>
  );
}
