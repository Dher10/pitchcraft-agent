"use client";

import type { PitchMixDatum } from "@/lib/types";
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
  data: PitchMixDatum[];
  awayStarterName: string;
  homeStarterName: string;
}

export default function PitchMixChart({
  data,
  awayStarterName,
  homeStarterName,
}: PitchMixChartProps) {
  return (
    <section className="rounded-lg border border-[#E5E8EC] bg-white p-5">
      <ChartHeading title="Pitch Mix" subtitle="Usage rate by pitch type" />
      <div className="mt-4 h-72 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 10, right: 8, left: -18, bottom: 0 }}>
            <CartesianGrid stroke="#E5E8EC" vertical={false} />
            <XAxis dataKey="pitch" tick={{ fill: "#5B6573", fontSize: 12 }} />
            <YAxis
              tick={{ fill: "#5B6573", fontSize: 12 }}
              tickFormatter={(value) => `${value}%`}
            />
            <Tooltip
              formatter={(value) => [`${value}%`, "Usage"]}
              contentStyle={{ borderColor: "#E5E8EC", borderRadius: 8 }}
            />
            <Legend wrapperStyle={{ fontSize: 12 }} />
            <Bar
              dataKey="away_starter_usage"
              name={awayStarterName}
              fill="#1B3A5B"
              radius={[4, 4, 0, 0]}
            />
            <Bar
              dataKey="home_starter_usage"
              name={homeStarterName}
              fill="#1E7A46"
              radius={[4, 4, 0, 0]}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}

function ChartHeading({ title, subtitle }: { title: string; subtitle: string }) {
  return (
    <div>
      <h3 className="font-display text-xl font-bold text-[#0F1722]">{title}</h3>
      <p className="mt-1 text-sm text-[#5B6573]">{subtitle}</p>
    </div>
  );
}
