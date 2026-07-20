import { AlertTriangle, Download } from "lucide-react";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useDeleteCompany, useExportCompanyData } from "@/features/settings/use-team";
import { extractErrorMessage } from "@/lib/api";
import { queryClient } from "@/lib/query";
import type { CompanyResponse } from "@/lib/api-types";

export function DangerZoneCard({ company }: { company: CompanyResponse }) {
  const navigate = useNavigate();
  const exportData = useExportCompanyData(company.id);
  const deleteCompany = useDeleteCompany(company.id);
  const [confirmName, setConfirmName] = useState("");

  const handleExport = () => {
    exportData.mutate(undefined, {
      onSuccess: (data) => {
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = url;
        link.download = `aurum-${company.id}-dados.json`;
        link.click();
        URL.revokeObjectURL(url);
        toast.success("Exportação concluída — o arquivo foi baixado.");
      },
      onError: (error) => toast.error(extractErrorMessage(error)),
    });
  };

  const handleDelete = () => {
    if (confirmName !== company.name) {
      toast.error("Digite o nome exato da empresa para confirmar.");
      return;
    }
    deleteCompany.mutate(undefined, {
      onSuccess: () => {
        toast.success("Empresa e todos os dados foram excluídos.");
        void queryClient.invalidateQueries({ queryKey: ["companies"] });
        navigate("/companies", { replace: true });
      },
      onError: (error) => toast.error(extractErrorMessage(error)),
    });
  };

  return (
    <Card className="mt-6 border-destructive/40">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <AlertTriangle className="size-4 text-destructive" /> Dados e privacidade (LGPD)
        </CardTitle>
        <CardDescription>
          Exporte todos os dados desta empresa ou exclua a empresa permanentemente. Ações de
          proprietário.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div>
            <p className="text-sm font-medium">Exportar meus dados</p>
            <p className="text-xs text-muted-foreground">
              Baixa um JSON com empresa, lançamentos, clientes, catálogo e mais.
            </p>
          </div>
          <Button variant="outline" onClick={handleExport} disabled={exportData.isPending}>
            <Download /> {exportData.isPending ? "Exportando…" : "Exportar"}
          </Button>
        </div>

        <div className="space-y-2 rounded-lg border border-destructive/40 bg-destructive/5 p-4">
          <p className="text-sm font-medium text-destructive">Excluir empresa</p>
          <p className="text-xs text-muted-foreground">
            Esta ação é irreversível. Todos os dados da empresa serão apagados. Para confirmar,
            digite <span className="font-medium">{company.name}</span> abaixo.
          </p>
          <div className="flex flex-wrap items-center gap-2 pt-1">
            <Label htmlFor="confirm-name" className="sr-only">
              Nome da empresa para confirmar
            </Label>
            <Input
              id="confirm-name"
              className="max-w-xs"
              placeholder={company.name}
              value={confirmName}
              onChange={(event) => setConfirmName(event.target.value)}
            />
            <Button
              variant="destructive"
              onClick={handleDelete}
              disabled={deleteCompany.isPending || confirmName !== company.name}
            >
              {deleteCompany.isPending ? "Excluindo…" : "Excluir empresa"}
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
