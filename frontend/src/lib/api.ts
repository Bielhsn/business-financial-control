import axios, { AxiosError, type InternalAxiosRequestConfig } from "axios";

import type { ApiErrorResponse, TokenResponse } from "@/lib/api-types";
import { getStoredRefreshToken, useAuthStore } from "@/stores/auth";

export const api = axios.create({
  baseURL: "/api/v1",
  timeout: 30_000,
});

api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

/** Uma única promise de refresh compartilhada evita corrida de N requisições 401 simultâneas. */
let refreshPromise: Promise<string | null> | null = null;

export async function refreshSession(): Promise<string | null> {
  if (refreshPromise === null) {
    refreshPromise = (async () => {
      const refreshToken = getStoredRefreshToken();
      if (refreshToken === null) {
        return null;
      }
      try {
        // axios "cru" (não `api`): o interceptor de 401 não deve tentar refresh do refresh.
        const { data } = await axios.post<TokenResponse>("/api/v1/auth/refresh", {
          refresh_token: refreshToken,
        });
        useAuthStore.getState().setSession({
          accessToken: data.access_token,
          refreshToken: data.refresh_token,
        });
        return data.access_token;
      } catch {
        useAuthStore.getState().clearSession();
        return null;
      } finally {
        refreshPromise = null;
      }
    })();
  }
  return refreshPromise;
}

interface RetriableConfig extends InternalAxiosRequestConfig {
  _retried?: boolean;
}

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError<ApiErrorResponse>) => {
    const config = error.config as RetriableConfig | undefined;
    const isAuthRoute = config?.url?.startsWith("/auth/") ?? false;
    if (error.response?.status === 401 && config && !config._retried && !isAuthRoute) {
      config._retried = true;
      const newToken = await refreshSession();
      if (newToken !== null) {
        config.headers.Authorization = `Bearer ${newToken}`;
        return api.request(config);
      }
    }
    return Promise.reject(error);
  },
);

/** Extrai a mensagem de erro padronizada do backend, com fallback amigável. */
export function extractErrorMessage(error: unknown): string {
  if (axios.isAxiosError<ApiErrorResponse>(error)) {
    const message = error.response?.data?.message;
    if (typeof message === "string" && message.length > 0) {
      return message;
    }
    if (error.code === "ERR_NETWORK") {
      return "Não foi possível conectar ao servidor. Verifique sua conexão.";
    }
  }
  return "Algo deu errado. Tente novamente.";
}
