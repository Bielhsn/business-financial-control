import { Loader2, MessageCircleQuestion, ScrollText, Send } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useAskQuestion, useGeneratePeriodSummary } from "@/features/dashboard/use-insights";
import { extractErrorMessage } from "@/lib/api";
import { BRAND } from "@/lib/brand";
import axios from "axios";

const SUGGESTED_QUESTIONS = [
  "Onde estou gastando mais?",
  "Por que meu lucro mudou?",
  "Meu ticket médio está bom?",
];

function aiErrorToast(error: unknown) {
  if (axios.isAxiosError(error) && error.response?.status === 503) {
    toast.error("Configure a chave do provedor de IA no backend para usar este recurso.");
  } else {
    toast.error(extractErrorMessage(error));
  }
}

export function SummaryCard({
  companyId,
  start,
  end,
}: {
  companyId: string;
  start: string;
  end: string;
}) {
  const generateSummary = useGeneratePeriodSummary(companyId);
  const [summary, setSummary] = useState<string | null>(null);

  return (
    <Card>
      <CardHeader>
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div>
            <CardTitle className="flex items-center gap-2 text-base">
              <ScrollText className="size-4 text-primary" /> Resumo executivo
            </CardTitle>
            <CardDescription>O período narrado em um parágrafo, pela IA.</CardDescription>
          </div>
          <Button
            variant="secondary"
            size="sm"
            disabled={generateSummary.isPending}
            onClick={() =>
              generateSummary.mutate(
                { start, end },
                {
                  onSuccess: (data) => setSummary(data.summary),
                  onError: aiErrorToast,
                },
              )
            }
          >
            {generateSummary.isPending ? (
              <>
                <Loader2 className="animate-spin" /> Escrevendo…
              </>
            ) : summary === null ? (
              "Gerar resumo"
            ) : (
              "Atualizar"
            )}
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        {summary === null ? (
          <p className="text-sm text-muted-foreground">
            Um parágrafo direto sobre como o período foi, o que pesou e a tendência.
          </p>
        ) : (
          <blockquote className="border-l-2 border-primary pl-4 text-sm leading-relaxed">
            {summary}
          </blockquote>
        )}
      </CardContent>
    </Card>
  );
}

export function AskCard({
  companyId,
  start,
  end,
}: {
  companyId: string;
  start: string;
  end: string;
}) {
  const askQuestion = useAskQuestion(companyId);
  const [question, setQuestion] = useState("");
  const [conversation, setConversation] = useState<{ question: string; answer: string } | null>(
    null,
  );

  const submit = (text: string) => {
    const normalized = text.trim();
    if (normalized.length < 3) {
      toast.error("Escreva uma pergunta um pouco mais completa.");
      return;
    }
    askQuestion.mutate(
      { start, end, question: normalized },
      {
        onSuccess: (data) => {
          setConversation({ question: normalized, answer: data.answer });
          setQuestion("");
        },
        onError: aiErrorToast,
      },
    );
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <MessageCircleQuestion className="size-4 text-primary" /> Pergunte à {BRAND.shortName}
        </CardTitle>
        <CardDescription>
          Perguntas em linguagem natural, respondidas só com os seus números do período.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        <form
          className="flex gap-2"
          onSubmit={(event) => {
            event.preventDefault();
            submit(question);
          }}
        >
          <Input
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            placeholder="Ex.: por que meu lucro caiu neste período?"
            aria-label="Pergunta sobre a empresa"
            maxLength={500}
          />
          <Button type="submit" size="icon" disabled={askQuestion.isPending} aria-label="Enviar">
            {askQuestion.isPending ? <Loader2 className="animate-spin" /> : <Send />}
          </Button>
        </form>

        {conversation === null && (
          <div className="flex flex-wrap gap-2">
            {SUGGESTED_QUESTIONS.map((suggestion) => (
              <button
                key={suggestion}
                type="button"
                onClick={() => submit(suggestion)}
                className="rounded-full border px-3 py-1 text-xs text-muted-foreground transition-colors hover:bg-accent hover:text-accent-foreground"
              >
                {suggestion}
              </button>
            ))}
          </div>
        )}

        {conversation !== null && (
          <div className="space-y-2 text-sm">
            <p className="font-medium">“{conversation.question}”</p>
            <p className="leading-relaxed text-muted-foreground">{conversation.answer}</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
