import { motion } from "framer-motion";
import { MailCheck } from "lucide-react";
import { Link, useSearchParams } from "react-router-dom";
import { toast } from "sonner";

import { AurumLogo } from "@/components/brand/logo";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useResendVerification } from "@/features/auth/use-auth";
import { extractErrorMessage } from "@/lib/api";

/**
 * Tela exibida logo após o cadastro: a conta fica bloqueada até a pessoa
 * confirmar o e-mail pelo link enviado. Permite reenviar o e-mail.
 */
export function CheckEmailPage() {
  const [searchParams] = useSearchParams();
  const email = searchParams.get("email") ?? "";
  const resend = useResendVerification();

  const onResend = () => {
    if (email === "") {
      return;
    }
    resend.mutate(email, {
      onSuccess: () => toast.success("Reenviamos o link de confirmação para o seu e-mail."),
      onError: (error) => toast.error(extractErrorMessage(error)),
    });
  };

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
          <CardHeader className="items-center text-center">
            <span className="mb-2 inline-flex h-12 w-12 items-center justify-center rounded-full bg-primary/10 text-primary">
              <MailCheck className="h-6 w-6" aria-hidden />
            </span>
            <CardTitle>Confirme seu e-mail</CardTitle>
            <CardDescription>
              Enviamos um link de confirmação{email !== "" ? ` para ${email}` : ""}. Clique no link
              do e-mail para ativar sua conta e liberar o acesso.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-center text-sm text-muted-foreground">
              Não recebeu? Verifique o spam ou reenvie abaixo.
            </p>
            <Button
              type="button"
              variant="outline"
              className="w-full"
              onClick={onResend}
              disabled={resend.isPending || email === ""}
            >
              {resend.isPending ? "Reenviando…" : "Reenviar e-mail"}
            </Button>
            <p className="text-center text-sm text-muted-foreground">
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
