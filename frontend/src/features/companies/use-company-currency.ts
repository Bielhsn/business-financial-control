import { useCompany } from "@/features/companies/use-companies";

/** Moeda da empresa ativa (ISO 4217). Fallback BRL enquanto a empresa carrega. */
export function useCompanyCurrency(companyId: string): string {
  const { data: company } = useCompany(companyId);
  return company?.currency ?? "BRL";
}
