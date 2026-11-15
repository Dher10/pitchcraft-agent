import type { SVGProps } from "react";

// Small line icons drawn inline, 12 to 18 px, `currentColor`. No icon library and no emoji; an icon always sits next to
// its word, except the Help button, which has an accessible name (docs/design/DESIGN_SYSTEM.md, "Iconography").

type IconProps = SVGProps<SVGSVGElement>;

function Svg({ children, ...props }: IconProps) {
  return (
    <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" {...props}>
      {children}
    </svg>
  );
}

export const CheckIcon = (props: IconProps) => <Svg {...props}><path d="M3 8.5l3.2 3L13 4.5" /></Svg>;
export const WarnIcon = (props: IconProps) => <Svg {...props}><path d="M8 2.2l6.2 11H1.8L8 2.2z" /><path d="M8 6.6v3.2M8 11.6v.1" /></Svg>;
export const CrossIcon = (props: IconProps) => <Svg {...props}><path d="M3.5 3.5l9 9M12.5 3.5l-9 9" /></Svg>;
export const DashIcon = (props: IconProps) => <Svg {...props}><path d="M3.5 8h9" /></Svg>;
export const InfoIcon = (props: IconProps) => <Svg {...props}><circle cx="8" cy="8" r="6" /><path d="M8 7.2v4M8 4.9v.1" /></Svg>;
export const HelpIcon = (props: IconProps) => <Svg {...props}><circle cx="8" cy="8" r="6.2" /><path d="M6.2 6.4a1.9 1.9 0 113.2 1.3c-.8.6-1.4.9-1.4 1.9M8 11.8v.1" /></Svg>;

export function LockIcon(props: IconProps) {
  return (
    <svg viewBox="0 0 12 12" aria-hidden="true" {...props}>
      <rect x="2.2" y="5.4" width="7.6" height="5.2" rx="1.2" fill="currentColor" />
      <path d="M4 5.4V3.9a2 2 0 014 0v1.5" fill="none" stroke="currentColor" strokeWidth="1.4" />
    </svg>
  );
}

/** The plate of the logo, dashed and with no zone: the symbol of an empty state. */
export function PlateIcon(props: IconProps) {
  return (
    <svg viewBox="0 0 44 44" fill="none" stroke="currentColor" strokeWidth="2" strokeDasharray="4 3" strokeLinejoin="round" aria-hidden="true" {...props}>
      <path d="M8 6h28a2 2 0 012 2v16a2 2 0 01-.7 1.5L23.3 38a2 2 0 01-2.6 0L6.7 25.5A2 2 0 016 24V8a2 2 0 012-2z" />
    </svg>
  );
}
