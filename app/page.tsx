import HomeOffSeason from "@/components/home/HomeOffSeason";
import PitchCraftApp from "@/components/PitchCraftApp";
import { getArchiveIndex, getArchiveItems, getPitchCraftData } from "@/lib/data";
import { homeView } from "@/lib/home";
import { seasonMode } from "@/lib/season";

interface HomeProps {
  searchParams: Promise<{ [key: string]: string | string[] | undefined }>;
}

export default async function Home({ searchParams }: HomeProps) {
  const [data, index] = await Promise.all([getPitchCraftData(), getArchiveIndex()]);
  // Off season with the archive there: the season in review. In season, or without the index, the daily view as before
  // (Today in season is frozen until February 2027, D67).
  if (index !== null && homeView(seasonMode(data), index) === "archive_home") return <HomeOffSeason index={index} />;

  const indexedArchive = await getArchiveItems(); // an existing but invalid index fails closed, as the interim home did
  const { matchup } = await searchParams;
  const initialSelectedId = Array.isArray(matchup) ? matchup[0] : matchup;
  return <PitchCraftApp data={data} initialSelectedId={initialSelectedId} indexedArchive={indexedArchive} />;
}
