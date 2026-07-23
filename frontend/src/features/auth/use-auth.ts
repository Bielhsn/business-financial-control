import { useMutation, useQuery } from "@tanstack/react-query";
import { useEffect } from "react";

import { api, refreshSession } from "@/lib/api";
import type { TokenResponse, UserResponse } from "@/lib/api-types";
import { queryClient } from "@/lib/query";
import { getStoredRefreshToken, useAuthStore } from "@/stores/auth";

interface LoginInput {
  email: string;
  password: string;
}

interface RegisterInput extends LoginInput {
  full_name: string;
}

export function useLogin() {
  const setSession = useAuthStore((s) => s.setSession);
  return useMutation({
    mutationFn: async (input: LoginInput) => {
      const { data } = await api.post<TokenResponse>("/auth/login", input);
      return data;
    },
    onSuccess: (data) => {
      setSession({ accessToken: data.access_token, refreshToken: data.refresh_token });
    },
  });
}

export function useRegister() {
  return useMutation({
    mutationFn: async (input: RegisterInput) => {
      const { data } = await api.post<UserResponse>("/auth/register", input);
      return data;
    },
  });
}

export function useGoogleLogin() {
  const setSession = useAuthStore((s) => s.setSession);
  return useMutation({
    mutationFn: async (idToken: string) => {
      const { data } = await api.post<TokenResponse>("/auth/google", { id_token: idToken });
      return data;
    },
    onSuccess: (data) => {
      setSession({ accessToken: data.access_token, refreshToken: data.refresh_token });
    },
  });
}

export function useForgotPassword() {
  return useMutation({
    mutationFn: async (email: string) => {
      await api.post("/auth/forgot-password", { email });
    },
  });
}

export function useResetPassword() {
  return useMutation({
    mutationFn: async (input: { email: string; token: string; new_password: string }) => {
      await api.post("/auth/reset-password", input);
    },
  });
}

export function useConfirmEmail() {
  return useMutation({
    mutationFn: async (input: { email: string; token: string }) => {
      await api.post("/auth/confirm-email", input);
    },
  });
}

export function useResendVerification() {
  return useMutation({
    mutationFn: async (email: string) => {
      await api.post("/auth/resend-verification", { email });
    },
  });
}

export function useChangePassword() {
  return useMutation({
    mutationFn: async (input: { current_password: string; new_password: string }) => {
      await api.post("/auth/change-password", input);
    },
  });
}

export function useRequestEmailVerification() {
  return useMutation({
    mutationFn: async () => {
      await api.post("/auth/request-verification");
    },
  });
}

export function useVerifyEmail() {
  return useMutation({
    mutationFn: async (code: string) => {
      await api.post("/auth/verify-email", { code });
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["auth", "me"] });
    },
  });
}

export function useLogout() {
  const clearSession = useAuthStore((s) => s.clearSession);
  return useMutation({
    mutationFn: async () => {
      const refreshToken = getStoredRefreshToken();
      if (refreshToken !== null) {
        // Melhor esforço: mesmo se a revogação falhar, a sessão local é encerrada.
        await api.post("/auth/logout", { refresh_token: refreshToken }).catch(() => undefined);
      }
    },
    onSettled: () => {
      clearSession();
      queryClient.clear();
    },
  });
}

export function useCurrentUser() {
  const accessToken = useAuthStore((s) => s.accessToken);
  const setUser = useAuthStore((s) => s.setUser);
  const query = useQuery({
    queryKey: ["auth", "me"],
    queryFn: async () => {
      const { data } = await api.get<UserResponse>("/auth/me");
      return data;
    },
    enabled: accessToken !== null,
    staleTime: 5 * 60_000,
  });

  useEffect(() => {
    setUser(query.data ?? null);
  }, [query.data, setUser]);

  return query;
}

/**
 * No boot da aplicação: se existe refresh token persistido, troca por uma sessão nova
 * (access token vive só em memória). Resolve `isBootstrapping` ao terminar.
 */
export function useSessionBootstrap() {
  const isBootstrapping = useAuthStore((s) => s.isBootstrapping);
  const setBootstrapped = useAuthStore((s) => s.setBootstrapped);

  useEffect(() => {
    if (!isBootstrapping) {
      return;
    }
    let cancelled = false;
    refreshSession().finally(() => {
      if (!cancelled) {
        setBootstrapped();
      }
    });
    return () => {
      cancelled = true;
    };
  }, [isBootstrapping, setBootstrapped]);

  return isBootstrapping;
}
