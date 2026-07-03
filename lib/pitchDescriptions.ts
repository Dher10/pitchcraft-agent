import type { PitchFamily } from "@/lib/types";

interface PitchDescriptionInput {
  family: PitchFamily;
  velocity: number | string;
  hBreak: number;
  vBreak: number;
}

export function describePitchMovement({ family, velocity, hBreak, vBreak }: PitchDescriptionInput) {
  const velo = typeof velocity === "number" ? velocity : Number.parseFloat(String(velocity));
  const hasVelo = Number.isFinite(velo);
  const horizontal = Math.abs(hBreak);
  const side = hBreak > 1.5 ? "arm-side" : hBreak < -1.5 ? "glove-side" : "mostly straight";

  if (family === "Fastball") {
    if (hasVelo && velo >= 95 && vBreak >= 14) {
      return `Rides through the zone with backspin and ${side} life, so it can look straight until it is past the hitter.`;
    }
    if (horizontal >= 11) {
      return `Runs ${side} with enough movement to miss the barrel even when the hitter sees fastball speed.`;
    }
    return `Shows a modest fastball shape with ${side} movement, built to get ahead and set up the next pitch.`;
  }

  if (family === "Breaking") {
    if (vBreak <= -8) {
      return `Drops hard late with ${side} bend, a shape built to fool hitters looking for a fastball.`;
    }
    if (horizontal >= 5) {
      return `Sweeps ${side} across the zone more than it dives, making the barrel chase sideways.`;
    }
    return `Breaks with a shorter tilt, giving the pitcher a different look without a huge drop.`;
  }

  if (hasVelo && velo <= 84) {
    return `Looks like a fastball out of the hand but arrives much slower, throwing off the hitter's timing.`;
  }
  if (horizontal >= 10) {
    return `Fades ${side} with fastball-like intent, useful for getting weak contact away from the barrel.`;
  }
  return `Changes speed more than shape, giving the hitter a timing problem after seeing harder pitches.`;
}
