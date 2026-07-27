import { useQuery } from "@tanstack/react-query";

import { api } from "@/lib/api";
import type { IntegrationCatalogItem } from "@/lib/api-types";

/**
 * Catálogo de integrações vindo do backend — fonte única.
 *
 * Antes o frontend mantinha um espelho manual de ~60 entradas, que saía de
 * sincronia a cada conector novo (a Hotmart, por exemplo, tinha conector
 * funcionando e nem aparecia na lista). O catálogo raramente muda, então cache
 * longo evita ida à rede a cada visita.
 */
export function useIntegrationCatalog() {
  return useQuery({
    queryKey: ["integrations", "catalog"],
    queryFn: async () => {
      const { data } = await api.get<{ items: IntegrationCatalogItem[] }>("/integrations/catalog");
      return data.items;
    },
    staleTime: 60 * 60_000,
  });
}
