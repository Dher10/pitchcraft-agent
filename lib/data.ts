import { promises as fs } from "fs";
import path from "path";
import type { PitchCraftData } from "./types";

export async function getPitchCraftData(): Promise<PitchCraftData> {
  const file = await fs.readFile(
    path.join(process.cwd(), "public", "data", "pitchcraft-demo.json"),
    "utf-8"
  );
  return JSON.parse(file) as PitchCraftData;
}
