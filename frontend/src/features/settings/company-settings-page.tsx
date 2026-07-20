import { useQuery } from "@tanstack/react-query";
import { Building2, History, Palette, Search, Trash2, Upload } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { useParams } from "react-router-dom";
import { toast } from "sonner";

import { PageHeader } from "@/components/page-header";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import {
  useCompany,
  useLookupCnpj,
  useUpdateCompany,
  type UpdateCompanyInput,
} from "@/features/companies/use-companies";
import type { CompanyResponse } from "@/lib/api-types";
import { api, extractErrorMessage } from "@/lib/api";
import { centsToInput, parseCurrencyToCents } from "@/lib/money";
import { readableForeground } from "@/lib/utils";

const MAX_LOGO_BYTES = 150 * 1024;

const ACTION_LABELS: Record<string, string> = {
  company_updated: "Empresa atualizada",
  blueprint_generated: "Blueprint gerado por IA",
  insights_generated: "Insights gerados",
  period_summary_generated: "Resumo executivo gerado",
  financial_question_asked: "Pergunta feita à IA",
  transaction_created: "Lançamento criado",
  transaction_marked_paid: "Lançamento pago",
  transaction_cancelled: "Lançamento cancelado",
  transactions_imported: "Extrato importado",
  stock_adjusted: "Estoque ajustado",
};

interface AuditEntry {
  id: string;
  user_id: string | null;
  action: string;
  details: Record<string, unknown>;
  created_at: string | null;
}

function AuditTrailCard({ companyId }: { companyId: string }) {
  const { data: entries } = useQuery({
    queryKey: ["companies", companyId, "audit-logs"],
    queryFn: async () => {
      const { data } = await api.get<AuditEntry[]>(`/companies/${companyId}/audit-logs`, {
        params: { limit: 20 },
      });
      return data;
    },
  });

  return (
    <Card className="mt-6">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <History className="size-4 text-primary" /> Atividade recente
        </CardTitle>
        <CardDescription>
          Trilha de auditoria das ações sensíveis nesta empresa (visível a proprietários e
          administradores).
        </CardDescription>
      </CardHeader>
      <CardContent>
        {(entries?.length ?? 0) === 0 ? (
          <p className="text-sm text-muted-foreground">Nenhuma atividade registrada ainda.</p>
        ) : (
          <ul className="space-y-2">
            {(entries ?? []).map((entry) => (
              <li key={entry.id} className="flex items-center justify-between gap-3 text-sm">
                <span>{ACTION_LABELS[entry.action] ?? entry.action}</span>
                <span className="shrink-0 text-xs text-muted-foreground">
                  {entry.created_at
                    ? new Date(entry.created_at).toLocaleString("pt-BR", {
                        day: "2-digit",
                        month: "2-digit",
                        hour: "2-digit",
                        minute: "2-digit",
                      })
                    : "—"}
                </span>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}

function CompanyProfileCard({ company }: { company: CompanyResponse }) {
  const updateCompany = useUpdateCompany(company.id);
  const lookupCnpj = useLookupCnpj();

  const [form, setForm] = useState({
    legal_name: company.legal_name ?? "",
    trade_name: company.trade_name ?? "",
    cnpj: company.cnpj ?? "",
    subsegment: company.subsegment ?? "",
    monthly_revenue:
      company.monthly_revenue_cents != null ? centsToInput(company.monthly_revenue_cents) : "",
    phone: company.phone ?? "",
    email: company.email ?? "",
    website: company.website ?? "",
  });

  const set = (key: keyof typeof form, value: string) =>
    setForm((current) => ({ ...current, [key]: value }));

  const handleLookup = () => {
    const digits = form.cnpj.replace(/\D/g, "");
    if (digits.length !== 14) {
      toast.error("Informe um CNPJ com 14 dígitos.");
      return;
    }
    lookupCnpj.mutate(digits, {
      onSuccess: (info) => {
        setForm((current) => ({
          ...current,
          cnpj: info.cnpj,
          legal_name: info.legal_name ?? current.legal_name,
          trade_name: info.trade_name ?? current.trade_name,
          email: info.email ?? current.email,
          phone: info.phone ?? current.phone,
        }));
        if (info.is_active) {
          toast.success(`CNPJ ${info.status ?? "encontrado"} — dados preenchidos.`);
        } else {
          toast.warning(`Atenção: situação cadastral "${info.status ?? "não ativa"}".`);
        }
      },
      onError: (error) => toast.error(extractErrorMessage(error)),
    });
  };

  const handleSave = () => {
    let revenueCents: number | null = null;
    if (form.monthly_revenue.trim()) {
      revenueCents = parseCurrencyToCents(form.monthly_revenue);
      if (revenueCents === null) {
        toast.error("Faturamento inválido — use o formato 1.234,56.");
        return;
      }
    }
    const payload: UpdateCompanyInput = {
      legal_name: form.legal_name.trim() || null,
      trade_name: form.trade_name.trim() || null,
      cnpj: form.cnpj.replace(/\D/g, "") || null,
      subsegment: form.subsegment.trim() || null,
      monthly_revenue_cents: revenueCents,
      phone: form.phone.trim() || null,
      email: form.email.trim() || null,
      website: form.website.trim() || null,
    };
    updateCompany.mutate(payload, {
      onSuccess: () => toast.success("Dados da empresa salvos!"),
      onError: (error) => toast.error(extractErrorMessage(error)),
    });
  };

  return (
    <Card className="mt-6">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <Building2 className="size-4 text-primary" /> Dados da empresa
        </CardTitle>
        <CardDescription>
          Informações fiscais e de contato. Informe o CNPJ e clique em “Buscar” para preencher
          automaticamente pela Receita.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="company-cnpj">CNPJ</Label>
          <div className="flex gap-2">
            <Input
              id="company-cnpj"
              inputMode="numeric"
              placeholder="00.000.000/0000-00"
              value={form.cnpj}
              onChange={(event) => set("cnpj", event.target.value)}
            />
            <Button
              type="button"
              variant="secondary"
              onClick={handleLookup}
              disabled={lookupCnpj.isPending}
            >
              <Search /> {lookupCnpj.isPending ? "Buscando…" : "Buscar"}
            </Button>
          </div>
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-2">
            <Label htmlFor="company-legal-name">Razão Social</Label>
            <Input
              id="company-legal-name"
              value={form.legal_name}
              onChange={(event) => set("legal_name", event.target.value)}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="company-trade-name">Nome Fantasia</Label>
            <Input
              id="company-trade-name"
              value={form.trade_name}
              onChange={(event) => set("trade_name", event.target.value)}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="company-subsegment">Subsegmento</Label>
            <Input
              id="company-subsegment"
              placeholder="Ex.: Cursos online"
              value={form.subsegment}
              onChange={(event) => set("subsegment", event.target.value)}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="company-revenue">Faturamento médio mensal (R$)</Label>
            <Input
              id="company-revenue"
              inputMode="decimal"
              placeholder="50.000,00"
              value={form.monthly_revenue}
              onChange={(event) => set("monthly_revenue", event.target.value)}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="company-phone">Telefone</Label>
            <Input
              id="company-phone"
              value={form.phone}
              onChange={(event) => set("phone", event.target.value)}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="company-email">E-mail</Label>
            <Input
              id="company-email"
              type="email"
              value={form.email}
              onChange={(event) => set("email", event.target.value)}
            />
          </div>
          <div className="space-y-2 sm:col-span-2">
            <Label htmlFor="company-website">Site</Label>
            <Input
              id="company-website"
              placeholder="https://…"
              value={form.website}
              onChange={(event) => set("website", event.target.value)}
            />
          </div>
        </div>

        <Button onClick={handleSave} disabled={updateCompany.isPending}>
          {updateCompany.isPending ? "Salvando…" : "Salvar dados"}
        </Button>
      </CardContent>
    </Card>
  );
}

const PRESET_COLORS = ["#B45309", "#4F46E5", "#0D9488", "#DC2626", "#DB2777", "#0F766E"];

export function CompanySettingsPage() {
  const { companyId } = useParams<{ companyId: string }>();
  const id = companyId ?? "";
  const { data: company, isLoading } = useCompany(id);
  const updateCompany = useUpdateCompany(id);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [logo, setLogo] = useState<string | null>(null);
  const [color, setColor] = useState<string | null>(null);
  const [theme, setTheme] = useState<"light" | "dark" | "none">("none");

  // Sincroniza o formulário quando a empresa carrega.
  useEffect(() => {
    if (company) {
      setLogo(company.brand_logo);
      setColor(company.brand_primary_color);
      setTheme(company.brand_theme ?? "none");
    }
  }, [company]);

  const handleLogoFile = (file: File | undefined) => {
    if (!file) {
      return;
    }
    if (!file.type.startsWith("image/")) {
      toast.error("Envie um arquivo de imagem (PNG, JPG, SVG…).");
      return;
    }
    if (file.size > MAX_LOGO_BYTES) {
      toast.error("Logo muito grande — use uma imagem de até 150 KB.");
      return;
    }
    const reader = new FileReader();
    reader.onload = () => setLogo(reader.result as string);
    reader.readAsDataURL(file);
  };

  const handleSave = () => {
    updateCompany.mutate(
      {
        brand_logo: logo,
        brand_primary_color: color,
        brand_theme: theme === "none" ? null : theme,
      },
      {
        onSuccess: () => toast.success("Aparência salva! O painel já está com a sua marca."),
        onError: (error) => toast.error(extractErrorMessage(error)),
      },
    );
  };

  if (isLoading) {
    return (
      <div className="mx-auto w-full max-w-3xl px-4 py-8">
        <Skeleton className="h-72 w-full" />
      </div>
    );
  }

  return (
    <div className="mx-auto w-full max-w-3xl px-4 py-8">
      <PageHeader
        title="Configurações"
        description="Deixe o painel com a cara da sua empresa. Somente proprietários e administradores podem salvar."
      />

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Palette className="size-4 text-primary" /> Aparência
          </CardTitle>
          <CardDescription>
            Logo, cor primária e tema padrão aplicados ao painel de {company?.name}.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Logo */}
          <div className="space-y-2">
            <Label>Logo da empresa</Label>
            <div className="flex items-center gap-4">
              <div className="flex size-16 items-center justify-center overflow-hidden rounded-lg border bg-background">
                {logo ? (
                  <img src={logo} alt="Logo da empresa" className="size-full object-contain" />
                ) : (
                  <Building2 className="size-7 text-muted-foreground" />
                )}
              </div>
              <div className="flex flex-wrap gap-2">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => fileInputRef.current?.click()}
                >
                  <Upload /> Enviar logo
                </Button>
                {logo && (
                  <Button type="button" variant="ghost" size="sm" onClick={() => setLogo(null)}>
                    <Trash2 /> Remover
                  </Button>
                )}
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/*"
                  className="hidden"
                  aria-label="Selecionar arquivo de logo"
                  onChange={(event) => handleLogoFile(event.target.files?.[0])}
                />
              </div>
            </div>
            <p className="text-xs text-muted-foreground">PNG, JPG ou SVG de até 150 KB.</p>
          </div>

          {/* Cor primária */}
          <div className="space-y-2">
            <Label htmlFor="brand-color">Cor primária</Label>
            <div className="flex flex-wrap items-center gap-2">
              {PRESET_COLORS.map((preset) => (
                <button
                  key={preset}
                  type="button"
                  aria-label={`Usar cor ${preset}`}
                  onClick={() => setColor(preset)}
                  className={
                    "size-8 rounded-full border-2 transition-transform hover:scale-110 " +
                    (color === preset ? "border-foreground" : "border-transparent")
                  }
                  style={{ backgroundColor: preset }}
                />
              ))}
              <input
                id="brand-color"
                type="color"
                value={color ?? "#B45309"}
                onChange={(event) => setColor(event.target.value)}
                className="size-8 cursor-pointer rounded-full border bg-transparent"
                aria-label="Escolher cor personalizada"
              />
              {color && (
                <Button type="button" variant="ghost" size="sm" onClick={() => setColor(null)}>
                  Usar cor padrão Aurum
                </Button>
              )}
            </div>
            {color && (
              <div
                className="mt-2 inline-flex items-center gap-2 rounded-md px-3 py-1.5 text-sm font-medium"
                style={{ backgroundColor: color, color: readableForeground(color) }}
              >
                Prévia de botão com a sua cor
              </div>
            )}
          </div>

          {/* Tema padrão */}
          <div className="space-y-2">
            <Label>Tema padrão da empresa</Label>
            <Select value={theme} onValueChange={(value) => setTheme(value as typeof theme)}>
              <SelectTrigger className="w-56" aria-label="Tema padrão">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="none">Seguir preferência do usuário</SelectItem>
                <SelectItem value="light">Claro</SelectItem>
                <SelectItem value="dark">Escuro</SelectItem>
              </SelectContent>
            </Select>
            <p className="text-xs text-muted-foreground">
              Aplicado a quem não escolheu um tema manualmente.
            </p>
          </div>

          <Button onClick={handleSave} disabled={updateCompany.isPending}>
            {updateCompany.isPending ? "Salvando…" : "Salvar aparência"}
          </Button>
        </CardContent>
      </Card>

      {company && <CompanyProfileCard company={company} />}

      <AuditTrailCard companyId={id} />
    </div>
  );
}
