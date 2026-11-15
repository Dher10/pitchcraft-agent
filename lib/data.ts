import { promises as fs } from "fs";
import path from "path";
import type { ArchiveItem, PitchCraftData } from "./types";
import { archiveIndexItems, parseArchiveIndex } from "./archiveIndex";

export async function getArchiveItems(): Promise<ArchiveItem[] | null> {
  let file: string;
  try {
    file = await fs.readFile(path.join(process.cwd(), "public", "data", "archive", "index-2026.json"), "utf-8");
  } catch (error) {
    if (typeof error === "object" && error !== null && "code" in error && error.code === "ENOENT") return null;
    throw new Error("archive_index_unreadable");
  }
  try {
    return archiveIndexItems(parseArchiveIndex(JSON.parse(file)));
  } catch {
    throw new Error("archive_index_invalid");
  }
}

export async function getPitchCraftData(): Promise<PitchCraftData> {
  const file = await fs.readFile(
    path.join(process.cwd(), "public", "data", "pitchcraft-demo.json"),
    "utf-8"
  );
  return JSON.parse(file) as PitchCraftData;
}
