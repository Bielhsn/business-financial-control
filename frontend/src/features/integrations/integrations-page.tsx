import { FileSpreadsheet, Plug, Sparkles, Upload } from "lucide-react";
import { useRef, useState } from "react";
import { useParams } from "react-router-dom";
import { toast } from "sonner";

import { PageHeader } from "@/components/page-header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useImportTransactions } from "@/features/integrations/use-import-transactions";
import { useCompanyCurrency } from "@/features/companies/use-company-currency";
import { extractErrorMessage } from "@/lib/api";
import { parseImportCsv, type ImportParseResult } from "@/lib/csv";
import { formatCents } from "@/lib/utils";

interface Connector {
  name: string;
  group: string;
}

/** Catálogo de conectores planejados — a infraestrutura de importação já existe;
 * cada conector é um adaptador sobre ela. */
const CONNECTOR_CATALOG: Connector[] = [
  { name: "iFood", group: "Delivery" },
  { name: "Rappi", group: "Delivery" },
  { name: "99Food", group: "Delivery" },
  { name: "Mercado Livre", group: "Marketplace" },
  { name: "Shopee", group: "Marketplace" },
  { name: "Amazon", group: "Marketplace" },
  { name: "Stripe", group: "Pagamentos" },
  { name: "Mercado Pago", group: "Pagamentos" },
  { name: "PagSeguro", group: "Pagamentos" },
  { name: "Asaas", group: "Pagamentos" },
  { name: "Nubank PJ", group: "Bancos" },
  { name: "Inter Empresas", group: "Bancos" },
  { name: "Itaú", group: "Bancos" },
  { name: "Omie", group: "Contabilidade" },
  { name: "Conta Azul", group: "Contabilidade" },
  { name: "Bling", group: "Contabilidade" },
  { name: "HubSpot", group: "CRM" },
  { name: "RD Station", group: "CRM" },
  { name: "WhatsApp Business", group: "Comunicação" },
  { name: "Slack", group: "Comunicação" },
  { name: "Google Calendar", group: "Google" },
  { name: "Google Analytics", group: "Google" },
];

function CsvImportCard({ companyId }: { companyId: string }) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const importTransactions = useImportTransactions(companyId);
  const currency = useCompanyCurrency(companyId);
  const [parsed, setParsed] = useState<ImportParseResult | null>(null);
  const [fileName, setFileName] = useState<string>("");

  const handleFile = (file: File | undefined) => {
    if (!file) {
      return;
    }
    setFileName(file.name);
    const reader = new FileReader();
    reader.onload = () => {
      const result = parseImportCsv(String(reader.result ?? ""));
      setParsed(result);
      if (result.rows.length === 0) {
        toast.error("Nenhuma linha válida encontrada no arquivo.");
      }
    };
    reader.readAsText(file);
  };

  const handleConfirm = () => {
    if (!parsed || parsed.rows.length === 0) {
      return;
    }
    importTransactions.mutate(parsed.rows, {
      onSuccess: (result) => {
        toast.success(
          `${result.imported} lançamentos importados` +
            (result.categories_created > 0
              ? ` (${result.categories_created} categorias criadas)`
              : ""),
        );
        setParsed(null);
        setFileName("");
      },
      onError: (error) => toast.error(extractErrorMessage(error)),
    });
  };

  return (
    <Card className="border-primary/40">
      <CardHeader>
        <div className="flex items-center justify-between gap-2">
          <CardTitle className="flex items-center gap-2 text-base">
            <FileSpreadsheet className="size-4 text-primary" /> Importar extrato (CSV)
          </CardTitle>
          <Badge variant="success">Disponível</Badge>
        </div>
        <CardDescription>
          Traga lançamentos do seu banco ou planilha: colunas data, descrição, valor (negativo =
          despesa) e categoria (opcional). Formatos de data DD/MM/AAAA ou AAAA-MM-DD.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex flex-wrap items-center gap-2">
          <Button variant="outline" size="sm" onClick={() => fileInputRef.current?.click()}>
            <Upload /> Escolher arquivo CSV
          </Button>
          {fileName && <span className="text-sm text-muted-foreground">{fileName}</span>}
          <input
            ref={fileInputRef}
            type="file"
            accept=".csv,text/csv"
            className="hidden"
            aria-label="Selecionar arquivo CSV"
            onChange={(event) => {
              handleFile(event.target.files?.[0]);
              event.target.value = "";
            }}
          />
        </div>

        {parsed && parsed.errors.length > 0 && (
          <div className="rounded-lg border border-destructive/40 bg-destructive/5 p-3 text-sm">
            <p className="font-medium text-destructive">
              {parsed.errors.length} linha(s) com problema (serão ignoradas):
            </p>
            <ul className="mt-1 list-inside list-disc text-muted-foreground">
              {parsed.errors.slice(0, 5).map((error) => (
                <li key={error}>{error}</li>
              ))}
              {parsed.errors.length > 5 && <li>… e mais {parsed.errors.length - 5}.</li>}
            </ul>
          </div>
        )}

        {parsed && parsed.rows.length > 0 && (
          <div className="space-y-3">
            <div className="overflow-x-auto rounded-lg border">
              <table className="w-full text-sm">
                <thead className="bg-muted/60 text-left text-xs text-muted-foreground">
                  <tr>
                    <th className="px-3 py-2 font-medium">Data</th>
                    <th className="px-3 py-2 font-medium">Descrição</th>
                    <th className="px-3 py-2 font-medium">Categoria</th>
                    <th className="px-3 py-2 text-right font-medium">Valor</th>
                  </tr>
                </thead>
                <tbody>
                  {parsed.rows.slice(0, 5).map((row, index) => (
                    <tr key={index} className="border-t">
                      <td className="px-3 py-2">
                        {new Date(row.date).toLocaleDateString("pt-BR")}
                      </td>
                      <td className="max-w-48 truncate px-3 py-2">{row.description}</td>
                      <td className="px-3 py-2 text-muted-foreground">
                        {row.category_name ?? "Importados"}
                      </td>
                      <td
                        className={
                          "px-3 py-2 text-right font-medium " +
                          (row.amount_cents > 0 ? "text-success" : "text-destructive")
                        }
                      >
                        {formatCents(row.amount_cents, currency)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="flex items-center justify-between">
              <p className="text-sm text-muted-foreground">
                {parsed.rows.length} lançamento(s) prontos para importar
                {parsed.rows.length > 5 ? " (mostrando os 5 primeiros)" : ""}.
              </p>
              <Button size="sm" onClick={handleConfirm} disabled={importTransactions.isPending}>
                {importTransactions.isPending
                  ? "Importando…"
                  : `Importar ${parsed.rows.length} lançamentos`}
              </Button>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export function IntegrationsPage() {
  const { companyId } = useParams<{ companyId: string }>();
  const id = companyId ?? "";
  const groups = [...new Set(CONNECTOR_CATALOG.map((c) => c.group))];

  return (
    <div className="mx-auto w-full max-w-4xl px-4 py-8">
      <PageHeader
        title="Integrações"
        description="Conecte as plataformas que a sua empresa já usa para alimentar o painel automaticamente."
      />

      <div className="space-y-6">
        <CsvImportCard companyId={id} />

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Sparkles className="size-4 text-primary" /> Inteligência artificial
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between rounded-lg border p-3">
              <div className="flex items-center gap-3">
                <div className="flex size-9 items-center justify-center rounded-lg bg-accent text-accent-foreground">
                  <Sparkles className="size-4" />
                </div>
                <div>
                  <p className="text-sm font-medium">Anthropic Claude</p>
                  <p className="text-xs text-muted-foreground">
                    Onboarding inteligente e insights financeiros
                  </p>
                </div>
              </div>
              <Badge variant="success">Integrado</Badge>
            </div>
          </CardContent>
        </Card>

        {groups.map((group) => (
          <Card key={group}>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <Plug className="size-4 text-primary" /> {group}
              </CardTitle>
            </CardHeader>
            <CardContent className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {CONNECTOR_CATALOG.filter((c) => c.group === group).map((connector) => (
                <div
                  key={connector.name}
                  className="flex items-center justify-between rounded-lg border p-3"
                >
                  <p className="text-sm font-medium">{connector.name}</p>
                  <Badge variant="muted">Em breve</Badge>
                </div>
              ))}
            </CardContent>
          </Card>
        ))}

        <p className="text-center text-xs text-muted-foreground">
          Precisa de um conector específico? Enquanto ele não chega, a importação CSV cobre qualquer
          plataforma que exporte planilhas.
        </p>
      </div>
    </div>
  );
}
