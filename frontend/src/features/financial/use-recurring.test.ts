import { describe, expect, it } from "vitest";

import { FREQUENCY_LABELS } from "@/features/financial/use-recurring";

describe("FREQUENCY_LABELS", () => {
  it("mapeia todas as periodicidades para rótulos em português", () => {
    expect(FREQUENCY_LABELS.weekly).toBe("Semanal");
    expect(FREQUENCY_LABELS.monthly).toBe("Mensal");
    expect(FREQUENCY_LABELS.yearly).toBe("Anual");
  });
});
