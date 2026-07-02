import { AlertTriangle, Lightbulb, Loader2, Sparkles, ThumbsUp } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useGenerateInsights } from "@/features/dashboard/use-insights";
import { extractErrorMessage } from "@/lib/api";
import type { InsightResponse } from "@/lib/api-types";
import { cn } from "@/lib/utils";
import axios from "axios";

const KIND_CONFIG = {
  highlight: { icon: ThumbsUp, label: "Destaque", className: "text-success bg-success/10" },
  warning: {
    icon: AlertTriangle,
    label: "Alerta",
    className: "text-destructive bg-destructive/10",
  },
  opportunity: { icon: Lightbulb, label: "Oportunidade", className: "text-primary bg-primary/10" },
} as const;

interface InsightsCardProps {
  companyId: string;
  start: string;
  end: string;
}

export function InsightsCard({ companyId, start, end }: InsightsCardProps) {
  const generateInsights = useGenerateInsights(companyId);
  const [insights, setInsights] = useState<InsightResponse[] | null>(null);
  const [aiUnavailable, setAiUnavailable] = useState(false);

  const handleGenerate = () => {
    generateInsights.mutate(
      { start, end },
      {
        onSuccess: (data) => {
          setInsights(data.insights);
          setAiUnavailable(false);
        },
        onError: (error) => {
          if (axios.isAxiosError(error) && error.response?.status === 503) {
            setAiUnavailable(true);
          } else {
            toast.error(extractErrorMessage(error));
          }
        },
      },
    );
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div>
            <CardTitle className="flex items-center gap-2 text-base">
              <Sparkles className="size-4 text-primary" /> Insights da IA
            </CardTitle>
            <CardDescription>
              Análise do período com base nos números já calculados — a IA interpreta, não calcula.
            </CardDescription>
          </div>
          <Button
            variant="secondary"
            size="sm"
            onClick={handleGenerate}
            disabled={generateInsights.isPending}
          >
            {generateInsights.isPending ? (
              <>
                <Loader2 className="animate-spin" /> Analisando…
              </>
            ) : insights === null ? (
              "Gerar insights"
            ) : (
              "Gerar novamente"
            )}
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        {aiUnavailable && (
          <p className="text-sm text-muted-foreground">
            O provedor de IA ainda não está configurado neste ambiente. Configure a
            `ANTHROPIC_API_KEY` no backend para habilitar os insights.
          </p>
        )}
        {!aiUnavailable && insights === null && !generateInsights.isPending && (
          <p className="text-sm text-muted-foreground">
            Clique em “Gerar insights” para receber destaques, alertas e oportunidades sobre o
            período selecionado.
          </p>
        )}
        {insights !== null && insights.length > 0 && (
          <div className="grid gap-3 sm:grid-cols-2">
            {insights.map((insight, index) => {
              const config = KIND_CONFIG[insight.kind];
              return (
                <div key={`${insight.kind}-${index}`} className="rounded-lg border p-4">
                  <div className="flex items-center gap-2">
                    <div
                      className={cn(
                        "flex size-7 items-center justify-center rounded-md",
                        config.className,
                      )}
                    >
                      <config.icon className="size-4" />
                    </div>
                    <p className="text-sm font-medium">{insight.title}</p>
                  </div>
                  <p className="mt-2 text-sm text-muted-foreground">{insight.message}</p>
                </div>
              );
            })}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
