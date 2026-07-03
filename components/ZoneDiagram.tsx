"use client";

import type { PitchLocation } from "@/lib/types";

interface ZoneDiagramProps {
  locations: PitchLocation[];
  width?: number;
  height?: number;
}

const pitchColors: Record<string, string> = {
  "Four-seam": "#D85A30",
  "Four-seam fastball": "#D85A30",
  Sinker: "#1D9E75",
  Slider: "#378ADD",
  Cutter: "#5B8DEF",
  Changeup: "#EF9F27",
  Curveball: "#7F77DD",
};

export function getPitchColor(pitch: string) {
  return pitchColors[pitch] ?? "#9E9E9E";
}

export default function ZoneDiagram({
  locations,
  width = 150,
  height = 178,
}: ZoneDiagramProps) {
  return (
    <svg
      role="img"
      aria-label="Pitch location strike zone"
      viewBox="0 0 160 190"
      width={width}
      height={height}
      className="overflow-visible"
    >
      <rect x="8" y="10" width="144" height="146" rx="6" fill="#fcfcfc" stroke="#e4e4e7" strokeWidth="1.5" />
      <rect x="40" y="34" width="80" height="100" rx="2" fill="none" stroke="#d4d4d8" strokeWidth="1.5" strokeDasharray="4 3" />
      <line x1="8" y1="60.6" x2="152" y2="60.6" stroke="#f1f1f2" strokeWidth="1" />
      <line x1="8" y1="105.3" x2="152" y2="105.3" stroke="#f1f1f2" strokeWidth="1" />
      <path d="M56 158 L80 145 L104 158 L96 174 L64 174 Z" fill="#ececed" stroke="#ececed" strokeWidth="1" />
      {locations.map((location, index) => {
        const svgX = 40 + location.x * 80;
        const svgY = 34 + location.y * 100;
        const color = getPitchColor(location.pitch);
        return (
          <g key={`${location.pitch}-${location.x}-${location.y}-${index}`}>
            <circle cx={svgX} cy={svgY} r="9" fill="#ffffff" />
            <circle cx={svgX} cy={svgY} r="7.5" fill={color}>
              <title>{location.pitch}</title>
            </circle>
          </g>
        );
      })}
    </svg>
  );
}
