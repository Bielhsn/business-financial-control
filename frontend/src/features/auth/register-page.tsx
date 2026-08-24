import { zodResolver } from "@hookform/resolvers/zod";
import { motion } from "framer-motion";
import { Check, Loader2, X } from "lucide-react";
import { useEffect, useState } from "react";
import { Controller, useForm } from "react-hook-form";
import { Link, useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { z } from "zod";

import { AurumLogo } from "@/components/brand/logo";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useLogin, useRegister } from "@/features/auth/use-auth";
import { useLookupCnpj } from "@/features/companies/use-companies";
import { extractErrorMessage } from "@/lib/api";
import { BRAND } from "@/lib/brand";
import { isValidCnpj, maskCnpj, onlyDigits } from "@/lib/cnpj";
import { assessPassword } from "@/lib/password-strength";

const registerSchema = z
  .object({
    company_name: z.string().min(1, "Informe o nome da empresa.").max(200),
    cnpj: z
      .string()
      .min(1, "Informe o CNPJ.")
      // Só os dígitos verificadores aqui. A existência real é confirmada pelo
      // servidor contra a Receita — o cliente não tem como garantir isso.
      .refine((value) => isValidCnpj(value), "CNPJ inválido — confira os números."),
    full_name: z.string().min(1, "Informe seu nome.").max(200),
    email: z.string().email("Informe um e-mail válido."),
    password: z.string().min(8, "A senha deve ter ao menos 8 caracteres.").max(128),
    password_confirmation: z.string().min(1, "Repita a senha."),
    phone: z.string().max(40).optional(),
    job_role: z.string().max(100).optional(),
  })
  .refine((data) => data.password === data.password_confirmation, {
    message: "As senhas não conferem.",
    path: ["password_confirmation"],
  });

/** Papéis oferecidos no cadastro. Servem para calibrar a linguagem do produto e
 * o contexto da IA — um dono e um contador da mesma empresa precisam de recortes
 * diferentes da mesma informação. */
const JOB_ROLES = [
  "Dono(a) do negócio",
  "Sócio(a)",
  "Gerente",
  "Financeiro",
  "Contador(a)",
  "Outro",
];

type RegisterForm = z.infer<typeof registerSchema>;

/** Barra de força da senha. Orienta antes do envio; quem autoriza é o servidor. */
function PasswordStrengthMeter({ password }: { password: string }) {
  const { strength, score, hint } = assessPassword(password);
  if (password.length === 0) {
    return null;
  }
  const cor =
    strength === "forte" ? "bg-success" : strength === "média" ? "bg-amber-500" : "bg-destructive";

  return (
    <div className="space-y-1">
      <div className="flex gap-1" aria-hidden="true">
        {[1, 2, 3, 4].map((nivel) => (
          <span
            key={nivel}
            className={`h-1 flex-1 rounded-full ${nivel <= score ? cor : "bg-muted"}`}
          />
        ))}
      </div>
      <p className="text-xs text-muted-foreground" aria-live="polite">
        Senha {strength}
        {hint && ` — ${hint}`}
      </p>
    </div>
  );
}

export function RegisterPage() {
  const navigate = useNavigate();
  const registerMutation = useRegister();
  const login = useLogin();
  const lookupCnpj = useLookupCnpj();
  const [empresaEncontrada, setEmpresaEncontrada] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    control,
    watch,
    setValue,
    formState: { errors },
  } = useForm<RegisterForm>({
    resolver: zodResolver(registerSchema),
    mode: "onBlur",
  });

  const cnpj = watch("cnpj") ?? "";
  const password = watch("password") ?? "";
  const passwordConfirmation = watch("password_confirmation") ?? "";
  const companyName = watch("company_name") ?? "";

  // Consulta a Receita assim que o CNPJ fica completo e válido. O objetivo é
  // confirmar que a empresa é a certa antes de a pessoa preencher o resto — e
  // poupar a digitação do nome quando a razão social já responde.
  useEffect(() => {
    const digits = onlyDigits(cnpj);
    if (digits.length !== 14 || !isValidCnpj(digits)) {
      setEmpresaEncontrada(null);
      return;
    }
    let cancelado = false;
    lookupCnpj.mutate(digits, {
      onSuccess: (info) => {
        if (cancelado) {
          return;
        }
        const nome = info.trade_name || info.legal_name;
        setEmpresaEncontrada(nome ?? null);
        // Não sobrescreve o que a pessoa já escreveu.
        if (nome && companyName.trim() === "") {
          setValue("company_name", nome, { shouldValidate: true });
        }
      },
      onError: () => {
        if (!cancelado) {
          setEmpresaEncontrada(null);
        }
      },
    });
    return () => {
      cancelado = true;
    };
    // `lookupCnpj` e `companyName` mudam a cada render/tecla; incluí-los
    // dispararia a consulta em loop.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cnpj, setValue]);

  const onSubmit = handleSubmit((values) => {
    registerMutation.mutate(
      { ...values, cnpj: onlyDigits(values.cnpj) },
      {
        onSuccess: (user) => {
          // Sem e-mail confirmado a conta fica bloqueada — leva para a tela que
          // explica isso em vez de tentar um login que vai falhar.
          if (!user.is_verified) {
            navigate(`/verifique-email?email=${encodeURIComponent(values.email)}`, {
              replace: true,
            });
            return;
          }
          login.mutate(
            { email: values.email, password: values.password },
            {
              // A empresa já existe; o onboarding completa o perfil dela.
              onSuccess: () => navigate("/companies", { replace: true }),
              onError: () => navigate("/login", { replace: true }),
            },
          );
        },
        onError: (error) => toast.error(extractErrorMessage(error)),
      },
    );
  });

  const isPending = registerMutation.isPending || login.isPending;
  const confirmacaoConfere = passwordConfirmation.length > 0 && password === passwordConfirmation;

  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4 py-8">
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3, ease: "easeOut" }}
        className="w-full max-w-md"
      >
        <div className="mb-6 flex flex-col items-center gap-2">
          <Link to="/" aria-label="Página inicial">
            <AurumLogo withProductSuffix />
          </Link>
          <p className="text-sm text-muted-foreground">{BRAND.slogan}</p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle className="font-display text-xl">Criar conta</CardTitle>
            <CardDescription>
              Em minutos você terá um painel financeiro sob medida para o seu negócio.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={onSubmit} className="space-y-4" noValidate>
              <div className="space-y-2">
                <Label htmlFor="cnpj">CNPJ da empresa</Label>
                <div className="relative">
                  <Controller
                    control={control}
                    name="cnpj"
                    render={({ field }) => (
                      <Input
                        id="cnpj"
                        inputMode="numeric"
                        placeholder="00.000.000/0000-00"
                        value={field.value ?? ""}
                        onChange={(event) => field.onChange(maskCnpj(event.target.value))}
                        onBlur={field.onBlur}
                      />
                    )}
                  />
                  {lookupCnpj.isPending && (
                    <Loader2
                      className="absolute right-3 top-1/2 size-4 -translate-y-1/2 animate-spin text-muted-foreground"
                      aria-label="Consultando CNPJ"
                    />
                  )}
                </div>
                {errors.cnpj && (
                  <p role="alert" className="text-sm text-destructive">
                    {errors.cnpj.message}
                  </p>
                )}
                {empresaEncontrada && !errors.cnpj && (
                  <p className="flex items-center gap-1.5 text-xs text-success">
                    <Check className="size-3.5" /> {empresaEncontrada}
                  </p>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor="company_name">Nome da empresa</Label>
                <Input
                  id="company_name"
                  placeholder="Como o negócio é conhecido"
                  {...register("company_name")}
                />
                {errors.company_name && (
                  <p role="alert" className="text-sm text-destructive">
                    {errors.company_name.message}
                  </p>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor="full_name">Seu nome completo</Label>
                <Input id="full_name" autoComplete="name" {...register("full_name")} />
                {errors.full_name && (
                  <p role="alert" className="text-sm text-destructive">
                    {errors.full_name.message}
                  </p>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor="email">E-mail</Label>
                <Input
                  id="email"
                  type="email"
                  autoComplete="email"
                  placeholder="voce@empresa.com.br"
                  {...register("email")}
                />
                {errors.email && (
                  <p role="alert" className="text-sm text-destructive">
                    {errors.email.message}
                  </p>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor="password">Senha</Label>
                <Input
                  id="password"
                  type="password"
                  autoComplete="new-password"
                  {...register("password")}
                />
                <PasswordStrengthMeter password={password} />
                {errors.password && (
                  <p role="alert" className="text-sm text-destructive">
                    {errors.password.message}
                  </p>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor="password_confirmation">Confirme a senha</Label>
                <div className="relative">
                  <Input
                    id="password_confirmation"
                    type="password"
                    autoComplete="new-password"
                    {...register("password_confirmation")}
                  />
                  {passwordConfirmation.length > 0 && (
                    <span className="absolute right-3 top-1/2 -translate-y-1/2">
                      {confirmacaoConfere ? (
                        <Check className="size-4 text-success" aria-label="As senhas conferem" />
                      ) : (
                        <X
                          className="size-4 text-destructive"
                          aria-label="As senhas não conferem"
                        />
                      )}
                    </span>
                  )}
                </div>
                {errors.password_confirmation && (
                  <p role="alert" className="text-sm text-destructive">
                    {errors.password_confirmation.message}
                  </p>
                )}
              </div>

              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="phone">Telefone (opcional)</Label>
                  <Input
                    id="phone"
                    type="tel"
                    autoComplete="tel"
                    placeholder="(11) 99999-8888"
                    {...register("phone")}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="job_role">Sua função (opcional)</Label>
                  <select
                    id="job_role"
                    className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                    {...register("job_role")}
                  >
                    <option value="">Prefiro não informar</option>
                    {JOB_ROLES.map((role) => (
                      <option key={role} value={role}>
                        {role}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <Button type="submit" className="w-full" disabled={isPending}>
                {isPending ? "Criando conta..." : "Criar conta"}
              </Button>
            </form>

            <p className="mt-4 text-center text-sm text-muted-foreground">
              Já tem conta?{" "}
              <Link to="/login" className="font-medium text-primary hover:underline">
                Entrar
              </Link>
            </p>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  );
}
