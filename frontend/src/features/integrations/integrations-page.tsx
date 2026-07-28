import { FileSpreadsheet, Plug, Sparkles, Upload, Wand2 } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { useParams, useSearchParams } from "react-router-dom";
import { toast } from "sonner";

import { PageHeader } from "@/components/page-header";
import { PaginatedList } from "@/components/paginated-list";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useBlueprint } from "@/features/blueprint/use-blueprint";
import {
  IntegrationActions,
  IntegrationStatusBadge,
} from "@/features/integrations/integration-actions";
import { useAvailableConnectors, useConnections } from "@/features/integrations/use-connectors";
import { SalesAnalyticsCard } from "@/features/integrations/sales-analytics-card";
import { useImportTransactions } from "@/features/integrations/use-import-transactions";
import { useCompanyCurrency } from "@/features/companies/use-company-currency";
import { extractErrorMessage } from "@/lib/api";
import { parseImportCsv, type ImportParseResult } from "@/lib/csv";
import type { IntegrationCatalogItem } from "@/lib/api-types";
import { useIntegrationCatalog } from "@/features/integrations/use-integration-catalog";
import { useSegmentProfileOrDefault } from "@/features/segment/use-segment-profile";
import { formatCents } from "@/lib/utils";

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

/**
 * Uma integração na listagem, com o estado verdadeiro da conexão.
 *
 * O mesmo componente serve a recomendadas e ao catálogo completo: a diferença
 * entre as duas listas é de curadoria, não de capacidade — se o conector existe,
 * dá para conectar dos dois lugares.
 */
function IntegrationRow({ item, companyId }: { item: IntegrationCatalogItem; companyId: string }) {
  const { data: connectors } = useAvailableConnectors(companyId);
  const { data: connections } = useConnections(companyId);

  const connector = item.provider
    ? (connectors ?? []).find((c) => c.provider === item.provider)
    : undefined;
  const connection = item.provider
    ? (connections ?? []).find((c) => c.provider === item.provider)
    : undefined;

  return (
    <div className="flex flex-wrap items-center justify-between gap-2 rounded-lg border p-3">
      <div className="min-w-0">
        <p className="flex flex-wrap items-center gap-2 text-sm font-medium">
          {item.name}
          <IntegrationStatusBadge connector={connector} connection={connection} />
        </p>
        <p className="text-xs text-muted-foreground">
          {connection?.last_synced_at
            ? `Última sincronização: ${new Date(connection.last_synced_at).toLocaleString("pt-BR")}`
            : item.group}
        </p>
        {connection?.status === "error" && connection.last_error && (
          <p className="mt-1 text-xs text-destructive">{connection.last_error}</p>
        )}
      </div>
      <IntegrationActions
        companyId={companyId}
        name={item.name}
        connector={connector}
        connection={connection}
      />
    </div>
  );
}

export function IntegrationsPage() {
  const { companyId } = useParams<{ companyId: string }>();
  const id = companyId ?? "";
  const { data: blueprint } = useBlueprint(id);
  const profile = useSegmentProfileOrDefault(id);
  // Catálogo do backend: fonte única, com o status real de cada integração.
  const { data: catalog } = useIntegrationCatalog();
  const allIntegrations = catalog ?? [];
  const catalogById = new Map(allIntegrations.map((item) => [item.id, item]));
  const [searchParams, setSearchParams] = useSearchParams();

  // Retorno do fluxo OAuth: mostra o resultado e limpa a URL.
  useEffect(() => {
    const connected = searchParams.get("connected");
    const failed = searchParams.get("integration_error");
    if (!connected && !failed) {
      return;
    }
    if (connected) {
      toast.success(`Integração ${connected} conectada com sucesso!`);
    } else {
      toast.error("Não foi possível concluir a conexão. Tente novamente.");
    }
    const next = new URLSearchParams(searchParams);
    next.delete("connected");
    next.delete("integration_error");
    setSearchParams(next, { replace: true });
  }, [searchParams, setSearchParams]);

  // Recomendação vem do PERFIL do segmento (determinístico) e, quando existe,
  // é refinada pelo blueprint da IA. Antes saía só da IA — por isso uma
  // barbearia via iFood sugerido quando o blueprint não existia ou errava.
  const recommendedIdList = [
    ...new Set([...profile.integrations, ...(blueprint?.integrations ?? [])]),
  ];
  const recommended = recommendedIdList
    .map((integrationId) => catalogById.get(integrationId))
    .filter((item): item is NonNullable<typeof item> => item !== undefined);
  const recommendedIds = new Set(recommended.map((item) => item.id));
  const others = allIntegrations.filter((item) => !recommendedIds.has(item.id));
  const otherGroups = [...new Set(others.map((item) => item.group))];

  return (
    <div className="mx-auto w-full max-w-4xl px-4 py-8">
      <PageHeader
        title="Integrações"
        description="Conecte as plataformas que a sua empresa já usa para alimentar o painel automaticamente."
      />

      <div className="space-y-6">
        <SalesAnalyticsCard companyId={id} />

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

        {recommended.length > 0 && (
          <Card className="border-primary/40">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <Wand2 className="size-4 text-primary" /> Recomendadas para o seu segmento
              </CardTitle>
              <CardDescription>
                Escolhidas pelo perfil do seu segmento — as conexões que fazem sentido para este
                tipo de negócio. As que já têm conector podem ser ligadas aqui mesmo.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {recommended.map((item) => (
                <IntegrationRow key={item.id} item={item} companyId={id} />
              ))}
            </CardContent>
          </Card>
        )}

        {recommended.length === 0 && (
          <Card>
            <CardContent className="py-6 text-center text-sm text-muted-foreground">
              Informe o segmento da empresa nas configurações para ver aqui as integrações
              recomendadas para o seu negócio.
            </CardContent>
          </Card>
        )}

        <details className="group">
          <summary className="cursor-pointer list-none">
            <div className="flex items-center justify-between rounded-xl border bg-card p-4 transition-colors hover:bg-accent/40">
              <div className="flex items-center gap-2 text-sm font-medium">
                <Plug className="size-4 text-primary" /> Todas as integrações do catálogo
                <span className="text-xs font-normal text-muted-foreground">({others.length})</span>
              </div>
              <span className="text-xs text-muted-foreground group-open:hidden">mostrar</span>
              <span className="hidden text-xs text-muted-foreground group-open:inline">
                ocultar
              </span>
            </div>
          </summary>
          <div className="mt-4 space-y-6">
            {otherGroups.map((group) => (
              <Card key={group}>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-base">
                    <Plug className="size-4 text-primary" /> {group}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <PaginatedList
                    items={others.filter((item) => item.group === group)}
                    label="integrações"
                    className="space-y-3"
                  >
                    {(item) => <IntegrationRow key={item.id} item={item} companyId={id} />}
                  </PaginatedList>
                </CardContent>
              </Card>
            ))}
          </div>
        </details>

        <p className="text-center text-xs text-muted-foreground">
          Precisa de um conector específico? Enquanto ele não chega, a importação CSV cobre qualquer
          plataforma que exporte planilhas.
        </p>
      </div>
    </div>
  );
}
