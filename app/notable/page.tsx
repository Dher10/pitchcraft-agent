import type { Metadata } from "next";
import NotableUnavailable from "@/components/notable/NotableUnavailable";
import NotableView from "@/components/notable/NotableView";
import { NOTABLE_COPY } from "@/lib/copy/notable";
import { getArchiveIndex } from "@/lib/data";
import { parseNotableQuery } from "@/lib/notableQuery";

export const metadata: Metadata = {
  title: `${NOTABLE_COPY.title} | PitchCraft`,
  description: NOTABLE_COPY.lede,
};

interface NotablePageProps {
  searchParams: Promise<{ [key: string]: string | string[] | undefined }>;
}

export default async function NotablePage({ searchParams }: NotablePageProps) {
  const index = await getArchiveIndex();
  // A missing or invalid index is a neutral notice, never an error page.
  if (index === null || index.games.length === 0) return <NotableUnavailable />;
  return <NotableView index={index} query={parseNotableQuery(await searchParams)} />;
}
