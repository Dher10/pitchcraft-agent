"use client";

import type { VelocityRow } from "@/lib/types";
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

interface VelocityChartProps {
  data: VelocityRow[];
  awayStarterName: string;
  homeStarterName: string;
}

export default function VelocityChart({ data, awayStarterName, homeStarterName }: VelocityChartProps) {
  return (
    <section className="rounded-xl border border-neutral-200 bg-white p-4">
      <h3 className="text-xl font-bold text-neutral-900">Velocity</h3>
      <p className="mt-1 text-sm text-neutral-500">Average by pitch type</p>
      <div className="mt-4" style={{ width: "100%", height: 280 }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 10, right: 8, left: -18, bottom: 0 }}>
            <CartesianGrid stroke="#e5e5e5" vertical={false} />
            <XAxis dataKey="pitch" tick={{ fill: "#737373", fontSize: 12 }} />
            <YAxis domain={["dataMin - 4", "dataMax + 4"]} tick={{ fill: "#737373", fontSize: 12 }} />
            <Tooltip formatter={(value) => [value === null ? "No value" : `${value} mph`, "Velocity"]} />
            <Legend wrapperStyle={{ fontSize: 12 }} />
            <Bar dataKey="away_starter_velocity" name={awayStarterName} fill="#1d4ed8" radius={[4, 4, 0, 0]} />
            <Bar dataKey="home_starter_velocity" name={homeStarterName} fill="#d97706" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}
