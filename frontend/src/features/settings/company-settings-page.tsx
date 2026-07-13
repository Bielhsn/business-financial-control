import { Building2, Palette, Trash2, Upload } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { useParams } from "react-router-dom";
import { toast } from "sonner";

import { PageHeader } from "@/components/page-header";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { useCompany, useUpdateCompany } from "@/features/companies/use-companies";
import { extractErrorMessage } from "@/lib/api";
import { readableForeground } from "@/lib/utils";

const MAX_LOGO_BYTES = 150 * 1024;

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
    </div>
  );
}
