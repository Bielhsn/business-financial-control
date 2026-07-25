/**
 * Normaliza um telefone brasileiro para o formato do link do WhatsApp (só
 * dígitos, com código do país 55). Retorna null se o número for curto demais.
 *
 * Regra: se já tiver 12+ dígitos começando com 55, assume que o código do país
 * já está presente; caso contrário, prefixa 55 (cobre o DDD 55 de Santa Maria,
 * cujos números têm 10–11 dígitos e ainda precisam do código do país).
 */
export function normalizeBrazilPhone(raw: string | null | undefined): string | null {
  if (!raw) {
    return null;
  }
  const digits = raw.replace(/\D/g, "");
  if (digits.length < 10) {
    return null;
  }
  if (digits.length >= 12 && digits.startsWith("55")) {
    return digits;
  }
  return `55${digits}`;
}

/**
 * Monta um link wa.me com a mensagem já preenchida. O barbeiro toca no link e o
 * WhatsApp abre com o texto pronto — é só apertar enviar. Retorna null quando o
 * telefone não é utilizável.
 */
export function buildWhatsappLink(
  phone: string | null | undefined,
  message: string,
): string | null {
  const normalized = normalizeBrazilPhone(phone);
  if (normalized === null) {
    return null;
  }
  return `https://wa.me/${normalized}?text=${encodeURIComponent(message)}`;
}

/** Texto usado quando a empresa ainda não escreveu a própria mensagem. */
export const DEFAULT_RETURN_MESSAGE =
  "Olá, {nome}! Tudo bem? Já faz um tempinho desde sua última visita na {empresa}. " +
  "Que tal agendar seu retorno? 😊";

/** Marcadores que o dono pode usar no texto da mensagem. */
export const RETURN_MESSAGE_PLACEHOLDERS = [
  { token: "{nome}", description: "primeiro nome do cliente" },
  { token: "{empresa}", description: "nome da sua empresa" },
  { token: "{dias}", description: "dias desde a última visita" },
] as const;

export interface ReturnMessageVars {
  clientName: string;
  companyName?: string | null;
  daysSinceVisit?: number | null;
}

/**
 * Troca os marcadores do modelo pelos dados do cliente. Só o primeiro nome é
 * usado em {nome} — soa mais natural na conversa do que o nome completo.
 */
export function renderReturnMessage(
  template: string | null | undefined,
  { clientName, companyName, daysSinceVisit }: ReturnMessageVars,
): string {
  const text = template && template.trim() !== "" ? template : DEFAULT_RETURN_MESSAGE;
  const firstName = clientName.trim().split(/\s+/)[0] ?? clientName;
  return (
    text
      .replaceAll("{nome}", firstName)
      .replaceAll("{empresa}", companyName ?? "")
      .replaceAll(
        "{dias}",
        daysSinceVisit === null || daysSinceVisit === undefined ? "" : String(daysSinceVisit),
      )
      // Remove espaços duplicados deixados por marcadores sem valor.
      .replace(/[ \t]{2,}/g, " ")
      .trim()
  );
}
