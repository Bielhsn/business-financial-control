import { describe, expect, it } from "vitest";

import { computeReturnStatus } from "@/lib/client-return";

const NOW = new Date("2026-07-24T12:00:00Z");

describe("computeReturnStatus", () => {
  it("sem cadência quando falta intervalo ou última visita", () => {
    expect(computeReturnStatus(null, 15, NOW).hasSchedule).toBe(false);
    expect(computeReturnStatus("2026-07-01T12:00:00Z", null, NOW).hasSchedule).toBe(false);
  });

  it("marca como na hora de voltar quando passou do intervalo", () => {
    const status = computeReturnStatus("2026-07-01T12:00:00Z", 15, NOW);
    expect(status.daysSinceVisit).toBe(23);
    expect(status.daysUntilDue).toBe(-8);
    expect(status.isDue).toBe(true);
  });

  it("ainda não é hora quando dentro do intervalo", () => {
    const status = computeReturnStatus("2026-07-20T12:00:00Z", 15, NOW);
    expect(status.daysSinceVisit).toBe(4);
    expect(status.daysUntilDue).toBe(11);
    expect(status.isDue).toBe(false);
  });

  it("é hora exatamente no dia do vencimento", () => {
    const status = computeReturnStatus("2026-07-09T12:00:00Z", 15, NOW);
    expect(status.daysUntilDue).toBe(0);
    expect(status.isDue).toBe(true);
  });
});
