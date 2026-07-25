import { motion } from "framer-motion";
import { CheckCircle2, Loader2, XCircle } from "lucide-react";
import { useEffect, useRef } from "react";
import { Link, useSearchParams } from "react-router-dom";

import { AurumLogo } from "@/components/brand/logo";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useConfirmEmail } from "@/features/auth/use-auth";

/**
 * Destino do link enviado por e-mail. Lê email+token da URL e confirma a conta
 * automaticamente ao abrir, mostrando sucesso ou erro (link inválido/expirado).
 */
export function VerifyEmailPage() {
  const [searchParams] = useSearchParams();
  const email = searchParams.get("email") ?? "";
  const token = searchParams.get("token") ?? "";
  const confirm = useConfirmEmail();

  // Dispara a confirmação uma única vez (StrictMode monta o efeito duas vezes).
  const startedRef = useRef(false);
  useEffect(() => {
    if (startedRef.current) {
      return;
    }
    startedRef.current = true;
    if (email !== "" && token !== "") {
      confirm.mutate({ email, token });
    }
  }, [email, token, confirm]);

  const missingParams = email === "" || token === "";
  const isError = missingParams || confirm.isError;
  const isSuccess = confirm.isSuccess;
  const isLoading = !isError && !isSuccess;

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
            {isLoading && (
              <span className="mb-2 inline-flex h-12 w-12 items-center justify-center rounded-full bg-primary/10 text-primary">
                <Loader2 className="h-6 w-6 animate-spin" aria-hidden />
              </span>
            )}
            {isSuccess && (
              <span className="mb-2 inline-flex h-12 w-12 items-center justify-center rounded-full bg-emerald-500/10 text-emerald-600">
                <CheckCircle2 className="h-6 w-6" aria-hidden />
              </span>
            )}
            {isError && (
              <span className="mb-2 inline-flex h-12 w-12 items-center justify-center rounded-full bg-destructive/10 text-destructive">
                <XCircle className="h-6 w-6" aria-hidden />
              </span>
            )}
            <CardTitle>
              {isLoading && "Confirmando seu e-mail…"}
              {isSuccess && "E-mail confirmado!"}
              {isError && "Não foi possível confirmar"}
            </CardTitle>
            <CardDescription>
              {isLoading && "Aguarde só um instante."}
              {isSuccess && "Sua conta está ativa. Agora é só entrar."}
              {isError &&
                "O link é inválido ou expirou. Solicite um novo e-mail de confirmação e tente novamente."}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {isSuccess && (
              <Button asChild className="w-full">
                <Link to="/login">Ir para o login</Link>
              </Button>
            )}
            {isError && (
              <Button asChild variant="outline" className="w-full">
                <Link to={`/verifique-email?email=${encodeURIComponent(email)}`}>
                  Reenviar confirmação
                </Link>
              </Button>
            )}
            {!isLoading && (
              <p className="text-center text-sm text-muted-foreground">
                <Link to="/login" className="text-primary hover:underline">
                  Voltar para o login
                </Link>
              </p>
            )}
          </CardContent>
        </Card>
      </motion.div>
    </div>
  );
}
