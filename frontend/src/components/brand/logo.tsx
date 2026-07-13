import { BRAND } from "@/lib/brand";
import { cn } from "@/lib/utils";

/** Monograma Aurum: "A" em traço fino dourado sobre grafite — legível de 16px a outdoor. */
export function AurumMark({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 32 32"
      role="img"
      aria-label={BRAND.shortName}
      className={cn("size-8", className)}
    >
      <defs>
        <linearGradient id="aurum-gold" x1="0" y1="1" x2="1" y2="0">
          <stop offset="0%" stopColor="#B45309" />
          <stop offset="55%" stopColor="#F59E0B" />
          <stop offset="100%" stopColor="#FDE68A" />
        </linearGradient>
      </defs>
      <rect width="32" height="32" rx="8" fill="#1C1917" />
      <path
        d="M 8.5 23 L 16 9 L 23.5 23"
        fill="none"
        stroke="url(#aurum-gold)"
        strokeWidth="2.4"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M 12.1 18.4 L 19.9 18.4"
        fill="none"
        stroke="url(#aurum-gold)"
        strokeWidth="2.4"
        strokeLinecap="round"
      />
    </svg>
  );
}

interface AurumLogoProps {
  className?: string;
  markClassName?: string;
  /** Exibe "OS" após o wordmark (contexto de produto, não de marca). */
  withProductSuffix?: boolean;
}

export function AurumLogo({ className, markClassName, withProductSuffix }: AurumLogoProps) {
  return (
    <span className={cn("inline-flex items-center gap-2.5", className)}>
      <AurumMark className={markClassName} />
      <span className="font-display text-xl font-semibold tracking-tight">
        {BRAND.shortName}
        {withProductSuffix && (
          <span className="ml-1.5 align-middle text-[0.6em] font-sans font-semibold uppercase tracking-widest text-muted-foreground">
            OS
          </span>
        )}
      </span>
    </span>
  );
}
