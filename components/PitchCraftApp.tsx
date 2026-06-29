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
  const selected =
    data.matchups.find((matchup) => matchup.id === selectedId) ??
    data.matchups.find((matchup) => matchup.id === data.featured_matchup_id) ??
    data.matchups[0];

  return (
    <main className="mx-auto flex max-w-3xl flex-col gap-6 px-4 py-8">
      <Hero />
      <GameCarousel
        matchups={data.matchups}
        archive={data.archive}
        featuredId={data.featured_matchup_id}
        selectedId={selected.id}
        onSelect={setSelectedId}
      />
      <MatchupView matchup={selected} />
      <AgentPipeline workflow={data.agent_workflow} />
      <ArchiveTable archive={data.archive} />
      <Disclaimer disclaimers={data.disclaimers} />
    </main>
  );
}
