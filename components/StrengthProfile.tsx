"use client";

import type { StrengthDatum } from "@/lib/types";
import {
  PolarAngleAxis,
  PolarGrid,
  PolarRadiusAxis,
  Radar,
  RadarChart,
  Legend,
  ResponsiveContainer,
  Tooltip,
} from "recharts";

interface StrengthProfileProps {
  data: StrengthDatum[];
  awayStarterName: string;
  homeStarterName: string;
}

export default function StrengthProfile({
  data,
  awayStarterName,
  homeStarterName,
}: StrengthProfileProps) {
  return (
    <section className="rounded-lg border border-[#E5E8EC] bg-white p-5">
      <div>
        <h3 className="font-display text-xl font-bold text-[#0F1722]">
          Strength Profile
        </h3>
        <p className="mt-1 text-sm text-[#5B6573]">PitchCraft signals, 0-100</p>
      </div>
      <div className="mt-4 h-72 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <RadarChart data={data} outerRadius="72%">
            <PolarGrid stroke="#E5E8EC" />
            <PolarAngleAxis
              dataKey="dimension"
              tick={{ fill: "#5B6573", fontSize: 12 }}
            />
            <PolarRadiusAxis
              angle={90}
              domain={[0, 100]}
              tick={{ fill: "#5B6573", fontSize: 11 }}
            />
            <Tooltip contentStyle={{ borderColor: "#E5E8EC", borderRadius: 8 }} />
            <Legend wrapperStyle={{ fontSize: 12 }} />
            <Radar
              dataKey="away_starter"
              name={awayStarterName}
              stroke="#1B3A5B"
              fill="#1B3A5B"
              fillOpacity={0.22}
            />
            <Radar
              dataKey="home_starter"
              name={homeStarterName}
              stroke="#1E7A46"
              fill="#1E7A46"
              fillOpacity={0.18}
            />
          </RadarChart>
        </ResponsiveContainer>
      </div>
      <p className="mt-3 text-xs leading-5 text-[#5B6573]">
        Stuff and Strength are PitchCraft internal signals, not official Stuff+.
      </p>
    </section>
  );
}
