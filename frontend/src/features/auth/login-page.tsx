import { zodResolver } from "@hookform/resolvers/zod";
import { motion } from "framer-motion";
import { useForm } from "react-hook-form";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { z } from "zod";

import { AurumLogo } from "@/components/brand/logo";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useLogin } from "@/features/auth/use-auth";
import { extractErrorMessage } from "@/lib/api";
import { BRAND } from "@/lib/brand";

const loginSchema = z.object({
  email: z.string().email("Informe um e-mail válido."),
  password: z.string().min(1, "Informe sua senha."),
});

type LoginForm = z.infer<typeof loginSchema>;

export function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const login = useLogin();
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginForm>({ resolver: zodResolver(loginSchema) });

  const onSubmit = handleSubmit((values) => {
    login.mutate(values, {
      onSuccess: () => {
        const redirectTo = (location.state as { from?: string } | null)?.from ?? "/companies";
        navigate(redirectTo, { replace: true });
      },
      onError: (error) => {
        toast.error(extractErrorMessage(error));
      },
    });
  });

  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4">
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3, ease: "easeOut" }}
        className="w-full max-w-sm"
      >
        <div className="mb-6 flex flex-col items-center gap-2">
          <Link to="/" aria-label="Página inicial">
            <AurumLogo withProductSuffix />
          </Link>
          <p className="text-sm text-muted-foreground">{BRAND.slogan}</p>
        </div>
        <Card>
          <CardHeader>
            <CardTitle className="font-display text-xl">Entrar</CardTitle>
            <CardDescription>Acesse o painel financeiro da sua empresa.</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={onSubmit} className="space-y-4" noValidate>
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
                  autoComplete="current-password"
                  {...register("password")}
                />
                {errors.password && (
                  <p role="alert" className="text-sm text-destructive">
                    {errors.password.message}
                  </p>
                )}
              </div>
              <Button type="submit" className="w-full" disabled={login.isPending}>
                {login.isPending ? "Entrando..." : "Entrar"}
              </Button>
            </form>
            <p className="mt-4 text-center text-sm text-muted-foreground">
              Não tem conta?{" "}
              <Link to="/register" className="font-medium text-primary hover:underline">
                Criar conta
              </Link>
            </p>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  );
}
