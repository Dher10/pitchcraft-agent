import { SITE_COPY } from "@/lib/copy/site";

/**
 * The mark (a home plate holding the strike zone, one cell lit) and the wordmark as live text (docs/design/assets/README.md).
 * On the board: plate in signal, cells in board, the lit cell in stitch.
 */
export default function Logo() {
  const cells = [
    [8.5, 6.0], [13.7, 6.0], [18.9, 6.0],
    [8.5, 10.4], [13.7, 10.4], [18.9, 10.4],
    [8.5, 14.8], [13.7, 14.8], [18.9, 14.8],
  ];
  return (
    <>
      <svg viewBox="0 0 32 32" aria-hidden="true" className="size-[30px] flex-none">
        <path
          d="M5 3.5h22a1.5 1.5 0 0 1 1.5 1.5v12.2a1.5 1.5 0 0 1-.5 1.1L17 29.2a1.5 1.5 0 0 1-2 0L4 18.3a1.5 1.5 0 0 1-.5-1.1V5A1.5 1.5 0 0 1 5 3.5z"
          fill="var(--color-signal)"
        />
        {cells.map(([x, y], index) => (
          <rect key={index} x={x} y={y} width="4.2" height="3.4" rx="0.8" fill={index === 8 ? "var(--color-stitch)" : "var(--color-board)"} />
        ))}
      </svg>
      {SITE_COPY.logo.wordmark}
    </>
  );
}
