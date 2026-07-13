import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/** Formata centavos como moeda (pt-BR / BRL). A API sempre trafega inteiros em centavos. */
export function formatCents(cents: number, currency = "BRL", locale = "pt-BR"): string {
  return new Intl.NumberFormat(locale, { style: "currency", currency }).format(cents / 100);
}

/**
 * Decide se texto sobre a cor dada deve ser claro ou escuro (WCAG luminância relativa).
 * Usado para calcular o --primary-foreground quando a empresa customiza a cor primária.
 */
export function readableForeground(hexColor: string): string {
  const hex = hexColor.replace("#", "");
  const r = parseInt(hex.slice(0, 2), 16) / 255;
  const g = parseInt(hex.slice(2, 4), 16) / 255;
  const b = parseInt(hex.slice(4, 6), 16) / 255;
  const linear = (c: number) => (c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4);
  const luminance = 0.2126 * linear(r) + 0.7152 * linear(g) + 0.0722 * linear(b);
  return luminance > 0.4 ? "#1c1917" : "#ffffff";
}

/** Formata percentual com sinal (ex.: +12,3% / -4,0%). */
export function formatPercent(value: number, locale = "pt-BR"): string {
  const formatted = new Intl.NumberFormat(locale, {
    maximumFractionDigits: 1,
    minimumFractionDigits: 1,
  }).format(value);
  return `${value > 0 ? "+" : ""}${formatted}%`;
}
