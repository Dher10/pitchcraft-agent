interface DisclaimerProps {
  disclaimers: string[];
}

export default function Disclaimer({ disclaimers }: DisclaimerProps) {
  return (
    <footer className="border-t border-neutral-200 pt-4 text-xs leading-5 text-neutral-500">
      <h2 className="font-bold uppercase tracking-widest text-neutral-600">Notes</h2>
      <ul className="mt-3 space-y-2">
        {disclaimers.map((disclaimer) => (
          <li key={disclaimer}>{disclaimer}</li>
        ))}
      </ul>
    </footer>
  );
}
