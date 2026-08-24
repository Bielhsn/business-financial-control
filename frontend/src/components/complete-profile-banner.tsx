/**
 * Aviso de perfil incompleto.
 *
 * Não é dispensável de propósito. Enquanto o segmento estiver vazio, o painel
 * inteiro está no modo genérico — esconder isso deixaria a pessoa concluindo
 * que o produto simplesmente não entende o negócio dela.
 *
 * Também não redireciona à força: quem acabou de se cadastrar pode querer olhar
 * antes de configurar, e sequestrar a navegação é pior que um aviso presente.
 */
import { Sparkles } from "lucide-react";
import { Link } from "react-router-dom";

import { Button } from "@/components/ui/button";

export function CompleteProfileBanner({ companyId }: { companyId: string }) {
  return (
    <div
      role="status"
      className="flex flex-wrap items-center justify-between gap-3 border-b border-primary/30 bg-accent/50 px-4 py-3"
    >
      <div className="flex min-w-0 items-start gap-2.5">
        <Sparkles className="mt-0.5 size-4 shrink-0 text-primary" />
        <div className="min-w-0">
          <p className="text-sm font-medium">Falta dizer qual é o seu ramo</p>
          <p className="text-xs text-muted-foreground">
            Com o segmento definido, o painel passa a usar os indicadores, as categorias e os termos
            do seu negócio — em vez dos genéricos.
          </p>
        </div>
      </div>
      {/* Vai para as configurações, não para o onboarding: aquele fluxo CRIA uma
          empresa, e mandar para lá geraria uma segunda em vez de completar esta.
          `asChild` aceita um único filho — o comentário fica fora de propósito. */}
      <Button asChild size="sm">
        <Link to={`/c/${companyId}/settings`}>Informar o ramo</Link>
      </Button>
    </div>
  );
}
