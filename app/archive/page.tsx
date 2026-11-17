import type { Metadata } from "next";
import ArchiveUnavailable from "@/components/archive/ArchiveUnavailable";
import ArchiveView from "@/components/archive/ArchiveView";
import { parseArchiveQuery } from "@/lib/archiveQuery";
import { ARCHIVE_COPY } from "@/lib/copy/archive";
import { getArchiveIndex } from "@/lib/data";

export const metadata: Metadata = {
  title: `${ARCHIVE_COPY.title} | PitchCraft`,
  description: ARCHIVE_COPY.lede,
};

interface ArchivePageProps {
  searchParams: Promise<{ [key: string]: string | string[] | undefined }>;
}

export default async function ArchivePage({ searchParams }: ArchivePageProps) {
  const index = await getArchiveIndex();
  // A missing or invalid index is a neutral notice, never an error page.
  if (index === null || index.games.length === 0) return <ArchiveUnavailable />;
  return <ArchiveView index={index} query={parseArchiveQuery(await searchParams, index)} />;
}
