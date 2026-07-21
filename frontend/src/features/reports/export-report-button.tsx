import { Download } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { useExportReport } from "@/features/reports/use-export-report";
import { extractErrorMessage } from "@/lib/api";

export function ExportReportButton({
  companyId,
  report,
  label = "Exportar CSV",
}: {
  companyId: string;
  report: "financial" | "sales";
  label?: string;
}) {
  const exportReport = useExportReport(companyId);

  return (
    <Button
      variant="outline"
      onClick={() =>
        exportReport.mutate(report, {
          onError: (error) => toast.error(extractErrorMessage(error)),
        })
      }
      disabled={exportReport.isPending}
    >
      <Download /> {exportReport.isPending ? "Exportando…" : label}
    </Button>
  );
}
