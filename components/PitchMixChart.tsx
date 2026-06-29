"use client";

import type { PitchMixRow } from "@/lib/types";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

interface PitchMixChartProps {
  data: PitchMixRow[];
  awayStarterName: string;
  homeStarterName: string;
}

export default function PitchMixChart({ data, awayStarterName, homeStarterName }: PitchMixChartProps) {
  const chartData = data.map((row) => ({
    pitch: row.pitch,
    away_starter_usage: row.away_starter.overall,
    home_starter_usage: row.home_starter.overall,
  }));

  return (
    <section className="rounded-xl border border-neutral-200 bg-white p-4">
      <h3 className="text-xl font-bold text-neutral-900">Pitch Mix</h3>
      <p className="mt-1 text-sm text-neutral-500">Overall usage by pitch type</p>
      <div className="mt-4" style={{ width: "100%", height: 280 }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} margin={{ top: 10, right: 8, left: -18, bottom: 0 }}>
            <CartesianGrid stroke="#e5e5e5" vertical={false} />
            <XAxis dataKey="pitch" tick={{ fill: "#737373", fontSize: 12 }} />
            <YAxis tick={{ fill: "#737373", fontSize: 12 }} tickFormatter={(value) => `${value}%`} />
            <Tooltip formatter={(value) => [`${value}%`, "Usage"]} />
            <Legend wrapperStyle={{ fontSize: 12 }} />
            <Bar dataKey="away_starter_usage" name={awayStarterName} fill="#1d4ed8" radius={[4, 4, 0, 0]} />
            <Bar dataKey="home_starter_usage" name={homeStarterName} fill="#16a34a" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}
