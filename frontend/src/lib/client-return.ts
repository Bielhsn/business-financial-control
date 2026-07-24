export interface ReturnStatus {
  /** Tem cadência definida (intervalo + última visita registrada). */
  hasSchedule: boolean;
  /** Dias desde o último atendimento (null sem visita registrada). */
  daysSinceVisit: number | null;
  /** Dias até a próxima visita esperada (negativo = atrasado; null sem cadência). */
  daysUntilDue: number | null;
  /** Já passou da hora de voltar. */
  isDue: boolean;
}

const MS_PER_DAY = 86_400_000;

/**
 * Calcula o status de retorno de um cliente a partir da última visita e da
 * cadência (a cada quantos dias). Pura e determinística para facilitar o teste.
 */
export function computeReturnStatus(
  lastVisitAt: string | null,
  intervalDays: number | null,
  now: Date = new Date(),
): ReturnStatus {
  if (lastVisitAt === null || intervalDays === null) {
    return { hasSchedule: false, daysSinceVisit: null, daysUntilDue: null, isDue: false };
  }
  const last = new Date(lastVisitAt).getTime();
  const daysSinceVisit = Math.floor((now.getTime() - last) / MS_PER_DAY);
  const daysUntilDue = intervalDays - daysSinceVisit;
  return {
    hasSchedule: true,
    daysSinceVisit,
    daysUntilDue,
    isDue: daysUntilDue <= 0,
  };
}
