import { useQuery } from "@tanstack/react-query";

import { api } from "@/lib/api";
import type { SegmentProfileResponse } from "@/lib/api-types";
import { GENERIC_SEGMENT_PROFILE } from "@/lib/segment";

/**
 * Perfil do segmento da empresa — a fonte da personalização profunda (rótulos,
 * módulos, campos aplicáveis, exemplos e KPIs). Vem do backend e é determinístico:
 * não depende de a IA estar configurada nem de o dono gerar o blueprint.
 */
export function useSegmentProfile(companyId: string) {
  return useQuery({
    queryKey: ["companies", companyId, "segment-profile"],
    queryFn: async () => {
      const { data } = await api.get<SegmentProfileResponse>(
        `/companies/${companyId}/segment-profile`,
      );
      return data;
    },
    enabled: companyId !== "",
    // O perfil muda só quando o dono altera o segmento da empresa.
    staleTime: 30 * 60_000,
  });
}

/**
 * Perfil com fallback: evita `profile?.x ?? "..."` espalhado pelas telas enquanto
 * a requisição não resolve.
 */
export function useSegmentProfileOrDefault(companyId: string): SegmentProfileResponse {
  const { data } = useSegmentProfile(companyId);
  if (!data) {
    return GENERIC_SEGMENT_PROFILE;
  }
  // Mescla sobre o perfil genérico: um payload parcial (backend mais antigo que
  // o frontend, campo novo ainda não publicado) preenche o que falta em vez de
  // quebrar a tela ao acessar terminology/catalog_fields.
  return {
    ...GENERIC_SEGMENT_PROFILE,
    ...data,
    terminology: { ...GENERIC_SEGMENT_PROFILE.terminology, ...data.terminology },
    catalog_fields: { ...GENERIC_SEGMENT_PROFILE.catalog_fields, ...data.catalog_fields },
  };
}
