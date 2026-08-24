/**
 * Quando o perfil da empresa ainda não diz o que ela é.
 *
 * O cadastro passou a criar a empresa junto com a conta, mas só com nome e
 * CNPJ — o segmento fica para o onboarding. Enquanto ele estiver vazio, a
 * empresa resolve para o perfil genérico: sem KPIs do ramo, sem categorias
 * certas, sem capacidades, com exemplos neutros.
 *
 * Isso torna inerte toda a personalização por segmento justamente para quem
 * acabou de chegar. A regra mora aqui, num lugar só, para a tela saber avisar
 * em vez de deixar a pessoa achar que o produto é assim mesmo.
 */
import type { CompanyResponse } from "@/lib/api-types";

/** O segmento é o que destrava módulos, terminologia, KPIs e categorias. Sem
 * ele o produto funciona, mas genérico — e é isso que precisa ser sinalizado. */
export function isProfileIncomplete(
  company: Pick<CompanyResponse, "segment"> | undefined,
): boolean {
  if (!company) {
    // Ainda carregando: não afirma incompletude para o aviso não piscar na tela.
    return false;
  }
  return company.segment.trim() === "";
}
