interface DisclaimerProps {
  disclaimers: string[];
}

export default function Disclaimer({ disclaimers }: DisclaimerProps) {
  return (
    <footer className="border-t border-[#E5E8EC] bg-white">
      <div className="mx-auto flex w-full max-w-6xl flex-col gap-4 px-5 py-8 text-sm leading-6 text-[#5B6573] sm:px-8 lg:px-10">
        <p className="font-semibold uppercase tracking-[0.16em] text-[#1B3A5B]">
          Notes
        </p>
        <ul className="grid gap-2 md:grid-cols-2">
          {disclaimers.map((disclaimer) => (
            <li key={disclaimer}>{disclaimer}</li>
          ))}
        </ul>
      </div>
    </footer>
  );
}
