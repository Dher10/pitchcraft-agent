import PitchCraftApp from "@/components/PitchCraftApp";
import { getArchiveItems, getPitchCraftData } from "@/lib/data";

interface HomeProps {
  searchParams: Promise<{ [key: string]: string | string[] | undefined }>;
}

export default async function Home({ searchParams }: HomeProps) {
  const [data, indexedArchive] = await Promise.all([getPitchCraftData(), getArchiveItems()]);
  const { matchup } = await searchParams;
  const initialSelectedId = Array.isArray(matchup) ? matchup[0] : matchup;

  return <PitchCraftApp data={data} initialSelectedId={initialSelectedId} indexedArchive={indexedArchive} />;
}
