"use client";

import type { StrengthRow } from "@/lib/types";
import {
  Legend,
  PolarAngleAxis,
  PolarGrid,
  PolarRadiusAxis,
  Radar,
  RadarChart,
  ResponsiveContainer,
  Tooltip,
} from "recharts";

interface StrengthProfileProps {
  data: StrengthRow[];
  awayStarterName: string;
  homeStarterName: string;
}

export default function StrengthProfile({ data, awayStarterName, homeStarterName }: StrengthProfileProps) {
  return (
    <section className="rounded-xl border border-neutral-200 bg-white p-4">
      <h3 className="text-xl font-bold text-neutral-900">Strength Profile</h3>
      <p className="mt-1 text-sm text-neutral-500">PitchCraft signals, 0-100</p>
      <div className="mt-4" style={{ width: "100%", height: 280 }}>
        <ResponsiveContainer width="100%" height="100%">
          <RadarChart data={data} outerRadius="72%">
            <PolarGrid stroke="#e5e5e5" />
            <PolarAngleAxis dataKey="dimension" tick={{ fill: "#737373", fontSize: 12 }} />
            <PolarRadiusAxis angle={90} domain={[0, 100]} tick={{ fill: "#737373", fontSize: 11 }} />
            <Tooltip />
            <Legend wrapperStyle={{ fontSize: 12 }} />
            <Radar dataKey="away_starter" name={awayStarterName} stroke="#1d4ed8" fill="#1d4ed8" fillOpacity={0.22} />
            <Radar dataKey="home_starter" name={homeStarterName} stroke="#16a34a" fill="#16a34a" fillOpacity={0.18} />
          </RadarChart>
        </ResponsiveContainer>
      </div>
      <p className="mt-3 text-xs leading-5 text-neutral-500">
        Stuff and Strength are PitchCraft internal signals, not official Stuff+.
      </p>
    </section>
  );
}
