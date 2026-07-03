interface DisclaimerProps {
  disclaimers: string[];
}

export default function Disclaimer({ disclaimers }: DisclaimerProps) {
  return (
    <footer className="border-t border-neutral-200 pt-4">
      <h2 className="font-mono text-[10px] font-semibold uppercase tracking-widest text-neutral-400">Notes</h2>
      <ul className="mt-2.5 space-y-1.5 text-[10.5px] leading-5 text-neutral-400">
        {disclaimers.map((disclaimer) => (
          <li key={disclaimer}>{disclaimer}</li>
        ))}
      </ul>
    </footer>
  );
}
