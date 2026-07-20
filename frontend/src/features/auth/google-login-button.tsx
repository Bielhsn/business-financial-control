import { useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";

import { useGoogleLogin } from "@/features/auth/use-auth";
import { extractErrorMessage } from "@/lib/api";

// Tipagem mínima do Google Identity Services (carregado sob demanda).
interface GoogleAccounts {
  id: {
    initialize: (config: {
      client_id: string;
      callback: (r: { credential: string }) => void;
    }) => void;
    renderButton: (parent: HTMLElement, options: Record<string, unknown>) => void;
  };
}
declare global {
  interface Window {
    google?: { accounts: GoogleAccounts };
  }
}

const CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID as string | undefined;
const GSI_SRC = "https://accounts.google.com/gsi/client";

function loadGsi(): Promise<void> {
  return new Promise((resolve, reject) => {
    if (window.google?.accounts) {
      resolve();
      return;
    }
    const existing = document.querySelector<HTMLScriptElement>(`script[src="${GSI_SRC}"]`);
    if (existing) {
      existing.addEventListener("load", () => resolve());
      existing.addEventListener("error", () => reject(new Error("Falha ao carregar o Google.")));
      return;
    }
    const script = document.createElement("script");
    script.src = GSI_SRC;
    script.async = true;
    script.onload = () => resolve();
    script.onerror = () => reject(new Error("Falha ao carregar o Google."));
    document.head.appendChild(script);
  });
}

/**
 * Botão "Entrar com Google". Renderiza null quando VITE_GOOGLE_CLIENT_ID não está
 * configurado, para o app funcionar normalmente sem o login social habilitado.
 */
export function GoogleLoginButton() {
  const containerRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();
  const googleLogin = useGoogleLogin();

  useEffect(() => {
    if (!CLIENT_ID || !containerRef.current) {
      return;
    }
    let cancelled = false;
    loadGsi()
      .then(() => {
        if (cancelled || !window.google?.accounts || !containerRef.current) {
          return;
        }
        window.google.accounts.id.initialize({
          client_id: CLIENT_ID,
          callback: (response) => {
            googleLogin.mutate(response.credential, {
              onSuccess: () => navigate("/companies", { replace: true }),
              onError: (error) => toast.error(extractErrorMessage(error)),
            });
          },
        });
        window.google.accounts.id.renderButton(containerRef.current, {
          theme: "outline",
          size: "large",
          width: 320,
          text: "continue_with",
          locale: "pt-BR",
        });
      })
      .catch(() => toast.error("Não foi possível carregar o login com Google."));
    return () => {
      cancelled = true;
    };
  }, [googleLogin, navigate]);

  if (!CLIENT_ID) {
    return null;
  }

  return (
    <div className="mt-4 flex flex-col items-center gap-2">
      <div className="flex w-full items-center gap-3">
        <span className="h-px flex-1 bg-border" />
        <span className="text-xs text-muted-foreground">ou</span>
        <span className="h-px flex-1 bg-border" />
      </div>
      <div ref={containerRef} />
    </div>
  );
}
