/** The dash shown wherever a figure is not available. */
export const UNAVAILABLE = "—";

/**
 * A season figure for display. "N/A", an empty string, null and undefined are all
 * "not available" and show as a dash; nothing is ever parsed into a number here.
 */
export function formatFigure(value: string | number | null | undefined): string {
  if (value === null || value === undefined) return UNAVAILABLE;
  const text = String(value).trim();
  return text === "" || text === "N/A" ? UNAVAILABLE : text;
}
