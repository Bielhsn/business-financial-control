import { BarChart3, Clock, Package, RefreshCcw, TrendingUp, Users } from "lucide-react";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useSalesAnalytics } from "@/features/integrations/use-sales-analytics";
import type { SalesAnalyticsResponse } from "@/lib/api-types";
import { formatCents } from "@/lib/utils";

const PROVIDER_LABELS: Record<string, string> = {
  hotmart: "Hotmart",
  mercadolivre: "Mercado Livre",
  shopify: "Shopify",
  ifood: "iFood",
};

function providerLabel(provider: string): string {
  return PROVIDER_LABELS[provider] ?? provider;
}

export function SalesAnalyticsCard({ companyId }: { companyId: string }) {
  const { data, isLoading } = useSalesAnalytics(companyId, 30);

  if (isLoading) {
    return <Skeleton className="h-64 w-full" />;
  }
  // Só aparece quando há vendas sincronizadas — não polui a tela vazia.
  if (!data || (data.total_orders === 0 && data.total_refunds === 0)) {
    return null;
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <BarChart3 className="size-4 text-primary" /> Análise de vendas (últimos 30 dias)
        </CardTitle>
        <CardDescription>
          Indicadores consolidados das plataformas conectadas — atualizados a cada sincronização.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <Metrics data={data} />
        <div className="grid gap-6 md:grid-cols-2">
          <TopProducts data={data} />
          <PeakHours data={data} />
        </div>
        {data.by_platform.length > 1 && <ByPlatform data={data} />}
      </CardContent>
    </Card>
  );
}

function Metrics({ data }: { data: SalesAnalyticsResponse }) {
  const tiles = [
    {
      icon: <TrendingUp className="size-4" />,
      label: "Faturamento líquido",
      value: formatCents(data.total_net_cents),
    },
    {
      icon: <Package className="size-4" />,
      label: "Ticket médio",
      value: formatCents(data.avg_ticket_cents),
    },
    { icon: <BarChart3 className="size-4" />, label: "Pedidos", value: String(data.total_orders) },
    {
      icon: <RefreshCcw className="size-4" />,
      label: "Reembolsos",
      value: String(data.total_refunds),
    },
    {
      icon: <Users className="size-4" />,
      label: "Clientes únicos",
      value: String(data.unique_buyers),
    },
  ];
  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
      {tiles.map((tile) => (
        <div key={tile.label} className="rounded-lg border p-3">
          <div className="mb-1 flex items-center gap-1.5 text-xs text-muted-foreground">
            {tile.icon}
            {tile.label}
          </div>
          <p className="text-lg font-semibold tracking-tight">{tile.value}</p>
        </div>
      ))}
    </div>
  );
}

function TopProducts({ data }: { data: SalesAnalyticsResponse }) {
  return (
    <div>
      <p className="mb-2 flex items-center gap-1.5 text-sm font-medium">
        <Package className="size-4 text-muted-foreground" /> Produtos mais vendidos
      </p>
      {data.top_products.length === 0 ? (
        <p className="text-xs text-muted-foreground">Sem vendas no período.</p>
      ) : (
        <ul className="space-y-1.5 text-sm">
          {data.top_products.map((product, index) => (
            <li key={product.product} className="flex items-center justify-between gap-2">
              <span className="truncate">
                <span className="text-muted-foreground">{index + 1}.</span> {product.product}
              </span>
              <span className="shrink-0 text-muted-foreground">
                {product.quantity}× · {formatCents(product.revenue_cents)}
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function PeakHours({ data }: { data: SalesAnalyticsResponse }) {
  const max = Math.max(1, ...data.peak_hours.map((h) => h.orders));
  return (
    <div>
      <p className="mb-2 flex items-center gap-1.5 text-sm font-medium">
        <Clock className="size-4 text-muted-foreground" /> Horários de pico
      </p>
      {data.peak_hours.length === 0 ? (
        <p className="text-xs text-muted-foreground">Sem vendas no período.</p>
      ) : (
        <ul className="space-y-1.5 text-sm">
          {data.peak_hours.map((hour) => (
            <li key={hour.hour} className="flex items-center gap-2">
              <span className="w-12 shrink-0 tabular-nums text-muted-foreground">
                {String(hour.hour).padStart(2, "0")}h
              </span>
              <div className="h-2 flex-1 overflow-hidden rounded-full bg-muted">
                <div
                  className="h-full rounded-full bg-primary"
                  style={{ width: `${Math.round((hour.orders / max) * 100)}%` }}
                />
              </div>
              <span className="w-8 shrink-0 text-right tabular-nums text-muted-foreground">
                {hour.orders}
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function ByPlatform({ data }: { data: SalesAnalyticsResponse }) {
  return (
    <div>
      <p className="mb-2 text-sm font-medium">Por plataforma</p>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-xs text-muted-foreground">
              <th className="pb-2 font-medium">Plataforma</th>
              <th className="pb-2 text-right font-medium">Líquido</th>
              <th className="pb-2 text-right font-medium">Pedidos</th>
              <th className="pb-2 text-right font-medium">Ticket médio</th>
              <th className="pb-2 text-right font-medium">Reembolsos</th>
            </tr>
          </thead>
          <tbody>
            {data.by_platform.map((platform) => (
              <tr key={platform.provider} className="border-t">
                <td className="py-2 font-medium">{providerLabel(platform.provider)}</td>
                <td className="py-2 text-right">{formatCents(platform.net_cents)}</td>
                <td className="py-2 text-right">{platform.orders}</td>
                <td className="py-2 text-right">{formatCents(platform.avg_ticket_cents)}</td>
                <td className="py-2 text-right">{platform.refunds}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
