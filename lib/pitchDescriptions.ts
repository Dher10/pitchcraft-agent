import type { PitchFamily } from "@/lib/types";

interface PitchDescriptionInput {
  family: PitchFamily | null;
  velocity: number | string;
  hBreak: number;
  vBreak: number;
}

export function describePitchMovement({ family, hBreak, vBreak }: PitchDescriptionInput) {
  // A pitch the family map does not know has no family, and none is inferred from its name.
  if (family === null) {
    return "This pitch is not in the pitch-family map, so no shape description is given.";
  }

  // Arm/glove wording needs a confirmed hand/sign convention from the Savant
  // CSV reference: https://baseballsavant.mlb.com/csv-docs . No such evidence
  // is available locally, so use P0.16-e's approved sideways fallback for all
  // hands. Describe published magnitudes only; velocity establishes no
  // comparison with another pitch. Zero vertical displacement is written up.
  return `Moves ${Math.abs(hBreak)} in. sideways and ${Math.abs(vBreak)} in. ${vBreak < 0 ? "down" : "up"} compared with a pitch thrown without spin.`;
}
