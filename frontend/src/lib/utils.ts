import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/** Formata centavos como moeda (pt-BR / BRL). A API sempre trafega inteiros em centavos. */
export function formatCents(cents: number, currency = "BRL", locale = "pt-BR"): string {
  return new Intl.NumberFormat(locale, { style: "currency", currency }).format(cents / 100);
}

/** Formata percentual com sinal (ex.: +12,3% / -4,0%). */
export function formatPercent(value: number, locale = "pt-BR"): string {
  const formatted = new Intl.NumberFormat(locale, {
    maximumFractionDigits: 1,
    minimumFractionDigits: 1,
  }).format(value);
  return `${value > 0 ? "+" : ""}${formatted}%`;
}
