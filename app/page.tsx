import PitchCraftApp from "@/components/PitchCraftApp";
import { getPitchCraftData } from "@/lib/data";

interface HomeProps {
  searchParams: Promise<{ [key: string]: string | string[] | undefined }>;
}

export default async function Home({ searchParams }: HomeProps) {
  const data = await getPitchCraftData();
  const { matchup } = await searchParams;
  const initialSelectedId = Array.isArray(matchup) ? matchup[0] : matchup;

  return <PitchCraftApp data={data} initialSelectedId={initialSelectedId} />;
}
