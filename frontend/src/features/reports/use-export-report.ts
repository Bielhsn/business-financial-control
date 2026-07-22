import { useMutation } from "@tanstack/react-query";

import { api } from "@/lib/api";

export type ReportKind = "financial" | "sales" | "income-statement" | "accounts";

const FILENAMES: Record<ReportKind, string> = {
  financial: "lancamentos.csv",
  sales: "vendas.csv",
  "income-statement": "dre.csv",
  accounts: "contas.csv",
};

/** Baixa um relatório CSV do backend (com o token de auth) e dispara o download
 * no navegador via blob. `report` casa com o arquivo servido pela API. */
export function useExportReport(companyId: string) {
  return useMutation({
    mutationFn: async (report: ReportKind) => {
      const { data } = await api.get(`/companies/${companyId}/reports/${report}.csv`, {
        responseType: "blob",
      });
      const url = URL.createObjectURL(data as Blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = FILENAMES[report];
      link.click();
      URL.revokeObjectURL(url);
    },
  });
}
