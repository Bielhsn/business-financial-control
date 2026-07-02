import { create } from "zustand";

import type { UserResponse } from "@/lib/api-types";

const REFRESH_TOKEN_KEY = "bfc-refresh-token";

/**
 * Access token fica apenas em memória (não sobrevive a reload — é reobtido via refresh).
 * Refresh token fica em localStorage: trade-off consciente enquanto o backend emite
 * tokens em JSON (a alternativa httpOnly cookie exigiria mudança de contrato). Mitigado
 * por rotação a cada uso + revogação server-side no logout.
 */
interface AuthState {
  accessToken: string | null;
  user: UserResponse | null;
  /** true enquanto a sessão inicial (refresh no boot) ainda não foi resolvida. */
  isBootstrapping: boolean;
  setSession: (tokens: { accessToken: string; refreshToken: string }) => void;
  setUser: (user: UserResponse | null) => void;
  setBootstrapped: () => void;
  clearSession: () => void;
}

export function getStoredRefreshToken(): string | null {
  try {
    return localStorage.getItem(REFRESH_TOKEN_KEY);
  } catch {
    return null;
  }
}

function storeRefreshToken(token: string | null): void {
  try {
    if (token === null) {
      localStorage.removeItem(REFRESH_TOKEN_KEY);
    } else {
      localStorage.setItem(REFRESH_TOKEN_KEY, token);
    }
  } catch {
    /* storage indisponível (ex.: modo privado restrito) — sessão vive só em memória */
  }
}

export const useAuthStore = create<AuthState>()((set) => ({
  accessToken: null,
  user: null,
  isBootstrapping: getStoredRefreshToken() !== null,
  setSession: ({ accessToken, refreshToken }) => {
    storeRefreshToken(refreshToken);
    set({ accessToken });
  },
  setUser: (user) => set({ user }),
  setBootstrapped: () => set({ isBootstrapping: false }),
  clearSession: () => {
    storeRefreshToken(null);
    set({ accessToken: null, user: null, isBootstrapping: false });
  },
}));
