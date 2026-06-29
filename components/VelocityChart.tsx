"use client";

import type { VelocityDatum } from "@/lib/types";
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
  data: VelocityDatum[];
  awayStarterName: string;
  homeStarterName: string;
}

export default function VelocityChart({
  data,
  awayStarterName,
  homeStarterName,
}: VelocityChartProps) {
  return (
    <section className="rounded-lg border border-[#E5E8EC] bg-white p-5">
      <div>
        <h3 className="font-display text-xl font-bold text-[#0F1722]">
          Velocity
        </h3>
        <p className="mt-1 text-sm text-[#5B6573]">Average by pitch type</p>
      </div>
      <div className="mt-4 h-72 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 10, right: 8, left: -18, bottom: 0 }}>
            <CartesianGrid stroke="#E5E8EC" vertical={false} />
            <XAxis dataKey="pitch" tick={{ fill: "#5B6573", fontSize: 12 }} />
            <YAxis
              domain={["dataMin - 4", "dataMax + 4"]}
              tick={{ fill: "#5B6573", fontSize: 12 }}
              tickFormatter={(value) => `${value}`}
            />
            <Tooltip
              formatter={(value) =>
                value === null ? ["No value", "Velocity"] : [`${value} mph`, "Velocity"]
              }
              contentStyle={{ borderColor: "#E5E8EC", borderRadius: 8 }}
            />
            <Legend wrapperStyle={{ fontSize: 12 }} />
            <Bar
              dataKey="away_starter_velocity"
              name={awayStarterName}
              fill="#1B3A5B"
              radius={[4, 4, 0, 0]}
            />
            <Bar
              dataKey="home_starter_velocity"
              name={homeStarterName}
              fill="#9A6B00"
              radius={[4, 4, 0, 0]}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}
