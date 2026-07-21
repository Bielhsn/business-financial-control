import { useMutation } from "@tanstack/react-query";

import { api } from "@/lib/api";

/** Baixa um relatório CSV do backend (com o token de auth) e dispara o download
 * no navegador via blob. `report` é o nome do arquivo servido pela API. */
export function useExportReport(companyId: string) {
  return useMutation({
    mutationFn: async (report: "financial" | "sales") => {
      const { data } = await api.get(`/companies/${companyId}/reports/${report}.csv`, {
        responseType: "blob",
      });
      const url = URL.createObjectURL(data as Blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = report === "financial" ? "lancamentos.csv" : "vendas.csv";
      link.click();
      URL.revokeObjectURL(url);
    },
  });
}
