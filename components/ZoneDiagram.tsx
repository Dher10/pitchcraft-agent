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
  width = 120,
  height = 142,
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
      <rect x="40" y="34" width="80" height="100" fill="#ffffff" stroke="#d4d4d4" strokeWidth="2" />
      {[1, 2].map((line) => (
        <g key={line} stroke="#e5e5e5" strokeWidth="1">
          <line x1={40 + line * (80 / 3)} y1="34" x2={40 + line * (80 / 3)} y2="134" />
          <line x1="40" y1={34 + line * (100 / 3)} x2="120" y2={34 + line * (100 / 3)} />
        </g>
      ))}
      <path d="M56 158 L80 145 L104 158 L96 174 L64 174 Z" fill="#fafafa" stroke="#d4d4d4" strokeWidth="2" />
      {locations.map((location, index) => {
        const svgX = 40 + location.x * 80;
        const svgY = 34 + location.y * 100;
        return (
          <circle
            key={`${location.pitch}-${location.x}-${location.y}-${index}`}
            cx={svgX}
            cy={svgY}
            r="10"
            fill={getPitchColor(location.pitch)}
            opacity="0.85"
          >
            <title>{location.pitch}</title>
          </circle>
        );
      })}
    </svg>
  );
}
