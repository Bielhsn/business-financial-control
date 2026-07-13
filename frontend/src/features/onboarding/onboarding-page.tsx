import { zodResolver } from "@hookform/resolvers/zod";
import { AnimatePresence, motion } from "framer-motion";
import {
  ArrowLeft,
  ArrowRight,
  Check,
  Import,
  LayoutGrid,
  Lightbulb,
  ListChecks,
  Loader2,
  Sparkles,
  UserSquare2,
} from "lucide-react";
import { useEffect, useState } from "react";
import { Controller, useForm } from "react-hook-form";
import { Link, useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { z } from "zod";

import { Badge } from "@/components/ui/badge";
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
import { Textarea } from "@/components/ui/textarea";
import {
  useGenerateBlueprint,
  useSeedCategoriesFromBlueprint,
} from "@/features/blueprint/use-blueprint";
import { useCreateCompany } from "@/features/companies/use-companies";
import { extractErrorMessage } from "@/lib/api";
import type { CompanyBlueprintResponse, CompanyResponse } from "@/lib/api-types";
import { moduleDescription, moduleLabel } from "@/lib/modules";
import axios from "axios";

const COMPANY_SIZES = ["MEI", "Microempresa", "Pequena", "Média", "Grande"];
const CURRENCIES = [
  { code: "BRL", label: "Real (R$)" },
  { code: "USD", label: "Dólar (US$)" },
  { code: "EUR", label: "Euro (€)" },
  { code: "GBP", label: "Libra (£)" },
];
const SALES_CHANNELS = [
  "Loja física",
  "E-commerce próprio",
  "Delivery/apps",
  "Marketplace",
  "WhatsApp/redes sociais",
  "B2B/contratos",
];
const SALES_MODES = [
  "Venda direta/balcão",
  "Agendamento",
  "Pedidos/comandas",
  "Assinatura/mensalidade",
  "Projetos/orçamentos",
];
const TAX_REGIMES = ["Simples Nacional", "MEI", "Lucro Presumido", "Lucro Real", "Outro"];

const companySchema = z.object({
  name: z.string().min(1, "Informe o nome da empresa.").max(200),
  segment: z.string().min(1, "Descreva o segmento do negócio.").max(200),
  size: z.string().min(1, "Selecione o porte."),
  employee_count: z
    .number({ invalid_type_error: "Informe um número." })
    .int()
    .min(0, "Não pode ser negativo."),
  average_customer_count: z
    .number({ invalid_type_error: "Informe um número." })
    .int()
    .min(0, "Não pode ser negativo."),
  city: z.string().min(1, "Informe a cidade.").max(200),
  state: z.string().min(1, "Informe o estado.").max(200),
  country: z.string().min(1, "Informe o país.").max(200),
  tax_regime: z.string().max(200).optional(),
  currency: z.string().min(1, "Selecione a moeda."),
  sales_channels: z.array(z.string()),
  sales_mode: z.string().optional(),
  main_offerings: z.string().max(1000).optional(),
  additional_info: z.string().max(2000).optional(),
});

type CompanyForm = z.infer<typeof companySchema>;

type WizardStep =
  | { step: "form" }
  | { step: "generating"; company: CompanyResponse }
  | {
      step: "result";
      company: CompanyResponse;
      blueprint: CompanyBlueprintResponse | null;
      aiUnavailable: boolean;
    };

function GeneratingIndicator({ companyName }: { companyName: string }) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.96 }}
      animate={{ opacity: 1, scale: 1 }}
      className="flex flex-col items-center gap-5 py-16 text-center"
    >
      <div className="relative">
        <div className="flex size-16 items-center justify-center rounded-2xl bg-primary/10 text-primary">
          <Sparkles className="size-8" />
        </div>
        <Loader2 className="absolute -bottom-1 -right-1 size-6 animate-spin text-primary" />
      </div>
      <div className="space-y-1">
        <p className="font-medium">A IA está montando o painel da {companyName}…</p>
        <p className="max-w-sm text-sm text-muted-foreground">
          Interpretando o segmento, escolhendo módulos, categorias financeiras, KPIs e campos
          personalizados para o seu negócio.
        </p>
      </div>
    </motion.div>
  );
}

export function OnboardingPage() {
  const navigate = useNavigate();
  const createCompany = useCreateCompany();
  const [wizard, setWizard] = useState<WizardStep>({ step: "form" });
  const companyId = wizard.step === "form" ? "" : wizard.company.id;
  const generateBlueprint = useGenerateBlueprint(companyId);
  const seedCategories = useSeedCategoriesFromBlueprint(companyId);
  const [categoriesImported, setCategoriesImported] = useState(false);

  const {
    register,
    handleSubmit,
    control,
    formState: { errors },
  } = useForm<CompanyForm>({
    resolver: zodResolver(companySchema),
    defaultValues: {
      country: "Brasil",
      employee_count: 1,
      average_customer_count: 0,
      size: "",
      tax_regime: "",
      currency: "BRL",
      sales_channels: [],
      sales_mode: "",
      main_offerings: "",
    },
  });

  const onSubmit = handleSubmit((values) => {
    createCompany.mutate(
      {
        name: values.name,
        segment: values.segment,
        employee_count: values.employee_count,
        average_customer_count: values.average_customer_count,
        city: values.city,
        state: values.state,
        country: values.country,
        size: values.size,
        tax_regime: values.tax_regime || null,
        additional_info: values.additional_info || null,
        currency: values.currency,
        sales_channels: values.sales_channels,
        sales_mode: values.sales_mode || null,
        main_offerings: values.main_offerings || null,
      },
      {
        onSuccess: (company) => {
          setWizard({ step: "generating", company });
        },
        onError: (error) => toast.error(extractErrorMessage(error)),
      },
    );
  });

  // Dispara a geração do blueprint assim que a empresa é criada (efeito, não render:
  // o StrictMode re-renderiza e uma mutação no corpo do componente dispararia duas vezes).
  const generateMutate = generateBlueprint.mutate;
  useEffect(() => {
    if (wizard.step !== "generating") {
      return;
    }
    const company = wizard.company;
    generateMutate(
      { additional_context: null },
      {
        onSuccess: (blueprint) => {
          setWizard({ step: "result", company, blueprint, aiUnavailable: false });
        },
        onError: (error) => {
          const aiUnavailable = axios.isAxiosError(error) && error.response?.status === 503;
          if (!aiUnavailable) {
            toast.error(extractErrorMessage(error));
          }
          setWizard({ step: "result", company, blueprint: null, aiUnavailable });
        },
      },
    );
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [wizard.step]);

  return (
    <div className="min-h-screen bg-background px-4 py-10">
      <div className="mx-auto w-full max-w-2xl">
        <div className="mb-6">
          <Button variant="ghost" size="sm" asChild>
            <Link to="/companies">
              <ArrowLeft /> Minhas empresas
            </Link>
          </Button>
        </div>

        <AnimatePresence mode="wait">
          {wizard.step === "form" && (
            <motion.div
              key="form"
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -12 }}
              transition={{ duration: 0.25 }}
            >
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-xl">
                    <Sparkles className="size-5 text-primary" /> Nova empresa
                  </CardTitle>
                  <CardDescription>
                    Conte sobre o seu negócio — qualquer segmento serve, de barbearia a fintech. A
                    IA usa essas respostas para montar um painel sob medida.
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <form onSubmit={onSubmit} className="space-y-4" noValidate>
                    <div className="space-y-2">
                      <Label htmlFor="name">Nome da empresa</Label>
                      <Input id="name" placeholder="Ex.: Barbearia do Zé" {...register("name")} />
                      {errors.name && (
                        <p role="alert" className="text-sm text-destructive">
                          {errors.name.message}
                        </p>
                      )}
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="segment">Segmento</Label>
                      <Input
                        id="segment"
                        placeholder="Ex.: barbearia, restaurante, clínica, empresa de software…"
                        {...register("segment")}
                      />
                      <p className="text-xs text-muted-foreground">
                        Descreva com suas palavras — a IA interpreta segmentos fora da lista.
                      </p>
                      {errors.segment && (
                        <p role="alert" className="text-sm text-destructive">
                          {errors.segment.message}
                        </p>
                      )}
                    </div>

                    <div className="grid gap-4 sm:grid-cols-2">
                      <div className="space-y-2">
                        <Label htmlFor="size">Porte</Label>
                        <Controller
                          control={control}
                          name="size"
                          render={({ field }) => (
                            <Select value={field.value} onValueChange={field.onChange}>
                              <SelectTrigger id="size">
                                <SelectValue placeholder="Selecione" />
                              </SelectTrigger>
                              <SelectContent>
                                {COMPANY_SIZES.map((size) => (
                                  <SelectItem key={size} value={size}>
                                    {size}
                                  </SelectItem>
                                ))}
                              </SelectContent>
                            </Select>
                          )}
                        />
                        {errors.size && (
                          <p role="alert" className="text-sm text-destructive">
                            {errors.size.message}
                          </p>
                        )}
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="tax_regime">Regime tributário (opcional)</Label>
                        <Controller
                          control={control}
                          name="tax_regime"
                          render={({ field }) => (
                            <Select value={field.value ?? ""} onValueChange={field.onChange}>
                              <SelectTrigger id="tax_regime">
                                <SelectValue placeholder="Selecione" />
                              </SelectTrigger>
                              <SelectContent>
                                {TAX_REGIMES.map((regime) => (
                                  <SelectItem key={regime} value={regime}>
                                    {regime}
                                  </SelectItem>
                                ))}
                              </SelectContent>
                            </Select>
                          )}
                        />
                      </div>
                    </div>

                    <div className="grid gap-4 sm:grid-cols-2">
                      <div className="space-y-2">
                        <Label htmlFor="employee_count">Nº de funcionários</Label>
                        <Input
                          id="employee_count"
                          type="number"
                          min={0}
                          {...register("employee_count", { valueAsNumber: true })}
                        />
                        {errors.employee_count && (
                          <p role="alert" className="text-sm text-destructive">
                            {errors.employee_count.message}
                          </p>
                        )}
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="average_customer_count">Clientes por mês (média)</Label>
                        <Input
                          id="average_customer_count"
                          type="number"
                          min={0}
                          {...register("average_customer_count", { valueAsNumber: true })}
                        />
                        {errors.average_customer_count && (
                          <p role="alert" className="text-sm text-destructive">
                            {errors.average_customer_count.message}
                          </p>
                        )}
                      </div>
                    </div>

                    <div className="grid gap-4 sm:grid-cols-3">
                      <div className="space-y-2 sm:col-span-1">
                        <Label htmlFor="city">Cidade</Label>
                        <Input id="city" {...register("city")} />
                        {errors.city && (
                          <p role="alert" className="text-sm text-destructive">
                            {errors.city.message}
                          </p>
                        )}
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="state">Estado</Label>
                        <Input id="state" placeholder="Ex.: SP" {...register("state")} />
                        {errors.state && (
                          <p role="alert" className="text-sm text-destructive">
                            {errors.state.message}
                          </p>
                        )}
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="country">País</Label>
                        <Input id="country" {...register("country")} />
                        {errors.country && (
                          <p role="alert" className="text-sm text-destructive">
                            {errors.country.message}
                          </p>
                        )}
                      </div>
                    </div>

                    <div className="grid gap-4 sm:grid-cols-2">
                      <div className="space-y-2">
                        <Label>Moeda</Label>
                        <Controller
                          control={control}
                          name="currency"
                          render={({ field }) => (
                            <Select value={field.value} onValueChange={field.onChange}>
                              <SelectTrigger aria-label="Moeda">
                                <SelectValue />
                              </SelectTrigger>
                              <SelectContent>
                                {CURRENCIES.map((currency) => (
                                  <SelectItem key={currency.code} value={currency.code}>
                                    {currency.label}
                                  </SelectItem>
                                ))}
                              </SelectContent>
                            </Select>
                          )}
                        />
                      </div>
                      <div className="space-y-2">
                        <Label>Como você vende? (opcional)</Label>
                        <Controller
                          control={control}
                          name="sales_mode"
                          render={({ field }) => (
                            <Select value={field.value ?? ""} onValueChange={field.onChange}>
                              <SelectTrigger aria-label="Forma de venda">
                                <SelectValue placeholder="Selecione" />
                              </SelectTrigger>
                              <SelectContent>
                                {SALES_MODES.map((mode) => (
                                  <SelectItem key={mode} value={mode}>
                                    {mode}
                                  </SelectItem>
                                ))}
                              </SelectContent>
                            </Select>
                          )}
                        />
                      </div>
                    </div>

                    <div className="space-y-2">
                      <Label>Canais de venda (opcional)</Label>
                      <Controller
                        control={control}
                        name="sales_channels"
                        render={({ field }) => (
                          <div className="flex flex-wrap gap-2">
                            {SALES_CHANNELS.map((channel) => {
                              const selected = field.value.includes(channel);
                              return (
                                <button
                                  key={channel}
                                  type="button"
                                  aria-pressed={selected}
                                  onClick={() =>
                                    field.onChange(
                                      selected
                                        ? field.value.filter((c) => c !== channel)
                                        : [...field.value, channel],
                                    )
                                  }
                                  className={
                                    "rounded-full border px-3 py-1.5 text-xs font-medium transition-colors " +
                                    (selected
                                      ? "border-primary bg-primary text-primary-foreground"
                                      : "bg-transparent text-muted-foreground hover:bg-accent hover:text-accent-foreground")
                                  }
                                >
                                  {channel}
                                </button>
                              );
                            })}
                          </div>
                        )}
                      />
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="main_offerings">O que você vende? (opcional)</Label>
                      <Textarea
                        id="main_offerings"
                        placeholder="Ex.: cortes, barba e venda de pomadas; hambúrgueres artesanais e bebidas…"
                        {...register("main_offerings")}
                      />
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="additional_info">
                        Algo mais que a IA deva saber? (opcional)
                      </Label>
                      <Textarea
                        id="additional_info"
                        placeholder="Ex.: trabalhamos por assinatura mensal; vendemos online e na loja física…"
                        {...register("additional_info")}
                      />
                    </div>

                    <Button type="submit" className="w-full" disabled={createCompany.isPending}>
                      {createCompany.isPending ? (
                        <>
                          <Loader2 className="animate-spin" /> Criando empresa…
                        </>
                      ) : (
                        <>
                          Criar empresa e gerar painel com IA <ArrowRight />
                        </>
                      )}
                    </Button>
                  </form>
                </CardContent>
              </Card>
            </motion.div>
          )}

          {wizard.step === "generating" && (
            <motion.div key="generating" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
              <Card>
                <CardContent>
                  <GeneratingIndicator companyName={wizard.company.name} />
                </CardContent>
              </Card>
            </motion.div>
          )}

          {wizard.step === "result" && (
            <motion.div
              key="result"
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.25 }}
              className="space-y-4"
            >
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-xl">
                    <Check className="size-5 text-success" /> {wizard.company.name} criada!
                  </CardTitle>
                  <CardDescription>
                    {wizard.blueprint
                      ? "A IA montou este painel para o seu segmento. Você pode ajustar tudo depois."
                      : wizard.aiUnavailable
                        ? "O provedor de IA ainda não está configurado neste ambiente — você pode gerar o blueprint depois, nas configurações da empresa."
                        : "Não foi possível gerar o blueprint agora — você pode tentar de novo depois."}
                  </CardDescription>
                </CardHeader>
              </Card>

              {wizard.blueprint && (
                <>
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2 text-base">
                        <LayoutGrid className="size-4 text-primary" /> Módulos ativados
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="grid gap-3 sm:grid-cols-2">
                      {wizard.blueprint.modules.map((moduleId) => (
                        <div key={moduleId} className="rounded-lg border p-3">
                          <p className="text-sm font-medium">{moduleLabel(moduleId)}</p>
                          <p className="text-xs text-muted-foreground">
                            {moduleDescription(moduleId)}
                          </p>
                        </div>
                      ))}
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2 text-base">
                        <ListChecks className="size-4 text-primary" /> Categorias financeiras
                        sugeridas
                      </CardTitle>
                      <CardDescription>
                        Importe agora para começar a lançar receitas e despesas já organizadas.
                      </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div className="flex flex-wrap gap-2">
                        {wizard.blueprint.financial_categories.map((category) => (
                          <Badge
                            key={`${category.type}-${category.name}`}
                            variant={category.type === "income" ? "success" : "destructive"}
                          >
                            {category.name}
                          </Badge>
                        ))}
                      </div>
                      <Button
                        variant="secondary"
                        size="sm"
                        disabled={seedCategories.isPending || categoriesImported}
                        onClick={() =>
                          seedCategories.mutate(undefined, {
                            onSuccess: () => {
                              setCategoriesImported(true);
                              toast.success("Categorias importadas!");
                            },
                            onError: (error) => toast.error(extractErrorMessage(error)),
                          })
                        }
                      >
                        {categoriesImported ? (
                          <>
                            <Check /> Categorias importadas
                          </>
                        ) : (
                          <>
                            <Import /> Importar categorias agora
                          </>
                        )}
                      </Button>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2 text-base">
                        <Lightbulb className="size-4 text-primary" /> Indicadores (KPIs)
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-3">
                      {wizard.blueprint.kpis.map((kpi) => (
                        <div key={kpi.key} className="rounded-lg border p-3">
                          <p className="text-sm font-medium">{kpi.name}</p>
                          <p className="text-xs text-muted-foreground">{kpi.description}</p>
                        </div>
                      ))}
                    </CardContent>
                  </Card>

                  {wizard.blueprint.client_custom_fields.length > 0 && (
                    <Card>
                      <CardHeader>
                        <CardTitle className="flex items-center gap-2 text-base">
                          <UserSquare2 className="size-4 text-primary" /> Campos personalizados de
                          cliente
                        </CardTitle>
                        <CardDescription>
                          O cadastro de clientes da sua empresa terá estes campos extras.
                        </CardDescription>
                      </CardHeader>
                      <CardContent className="flex flex-wrap gap-2">
                        {wizard.blueprint.client_custom_fields.map((field) => (
                          <Badge key={field.key} variant="secondary">
                            {field.label}
                          </Badge>
                        ))}
                      </CardContent>
                    </Card>
                  )}
                </>
              )}

              <Button className="w-full" size="lg" onClick={() => navigate(`/c/${companyId}`)}>
                Abrir painel <ArrowRight />
              </Button>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
