/**
 * Converte entrada de moeda em pt-BR ("1.234,56", "1234,56", "1234.56", "1234")
 * para centavos (inteiro). A API só trafega inteiros — nunca float de dinheiro.
 * Retorna null para entrada inválida.
 */
export function parseCurrencyToCents(raw: string): number | null {
  const trimmed = raw.trim().replace(/^R\$\s*/i, "");
  if (trimmed === "") {
    return null;
  }
  let normalized = trimmed;
  const hasComma = trimmed.includes(",");
  const hasDot = trimmed.includes(".");
  if (hasComma) {
    // Formato brasileiro: ponto é separador de milhar, vírgula é decimal.
    normalized = trimmed.replace(/\./g, "").replace(",", ".");
  } else if (hasDot) {
    // Sem vírgula: um único ponto com 1-2 casas é decimal ("1234.56");
    // caso contrário, trata pontos como milhar ("1.234").
    const decimalLike = /^\d+\.\d{1,2}$/.test(trimmed);
    if (!decimalLike) {
      normalized = trimmed.replace(/\./g, "");
    }
  }
  if (!/^-?\d+(\.\d{1,2})?$/.test(normalized)) {
    return null;
  }
  const value = Number(normalized);
  if (!Number.isFinite(value)) {
    return null;
  }
  return Math.round(value * 100);
}

/** Formata centavos para edição em input ("123456" → "1234,56"). */
export function centsToInput(cents: number): string {
  return (cents / 100).toFixed(2).replace(".", ",");
}
