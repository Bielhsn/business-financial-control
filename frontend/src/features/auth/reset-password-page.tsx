import { zodResolver } from "@hookform/resolvers/zod";
import { motion } from "framer-motion";
import { useForm } from "react-hook-form";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { toast } from "sonner";
import { z } from "zod";

import { AurumLogo } from "@/components/brand/logo";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useResetPassword } from "@/features/auth/use-auth";
import { extractErrorMessage } from "@/lib/api";

const schema = z.object({
  email: z.string().email("Informe um e-mail válido."),
  token: z.string().min(1, "Link inválido. Solicite um novo e-mail de redefinição."),
  new_password: z.string().min(8, "A senha deve ter ao menos 8 caracteres."),
});
type FormValues = z.infer<typeof schema>;

export function ResetPasswordPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const resetPassword = useResetPassword();
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      email: searchParams.get("email") ?? "",
      token: searchParams.get("token") ?? "",
    },
  });

  const onSubmit = handleSubmit((values) => {
    resetPassword.mutate(values, {
      onSuccess: () => {
        toast.success("Senha redefinida! Faça login com a nova senha.");
        navigate("/login", { replace: true });
      },
      onError: (error) => toast.error(extractErrorMessage(error)),
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
        </div>
        <Card>
          <CardHeader>
            <CardTitle>Redefinir senha</CardTitle>
            <CardDescription>
              Escolha uma nova senha para a sua conta. Abrimos esta página a partir do link enviado
              para o seu e-mail.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={onSubmit} className="space-y-4" noValidate>
              <input type="hidden" {...register("token")} />
              <div className="space-y-2">
                <Label htmlFor="email">E-mail</Label>
                <Input id="email" type="email" autoComplete="email" {...register("email")} />
                {errors.email && (
                  <p role="alert" className="text-sm text-destructive">
                    {errors.email.message}
                  </p>
                )}
              </div>
              {errors.token && (
                <p role="alert" className="text-sm text-destructive">
                  {errors.token.message}
                </p>
              )}
              <div className="space-y-2">
                <Label htmlFor="new_password">Nova senha</Label>
                <Input
                  id="new_password"
                  type="password"
                  autoComplete="new-password"
                  {...register("new_password")}
                />
                {errors.new_password && (
                  <p role="alert" className="text-sm text-destructive">
                    {errors.new_password.message}
                  </p>
                )}
              </div>
              <Button type="submit" className="w-full" disabled={resetPassword.isPending}>
                {resetPassword.isPending ? "Redefinindo…" : "Redefinir senha"}
              </Button>
            </form>
            <p className="mt-4 text-center text-sm text-muted-foreground">
              <Link to="/login" className="text-primary hover:underline">
                Voltar para o login
              </Link>
            </p>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  );
}
