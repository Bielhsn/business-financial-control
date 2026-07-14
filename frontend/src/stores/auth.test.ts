import { beforeEach, describe, expect, it } from "vitest";

import { getStoredRefreshToken, useAuthStore } from "@/stores/auth";

describe("auth store", () => {
  beforeEach(() => {
    localStorage.clear();
    useAuthStore.setState({ accessToken: null, user: null, isBootstrapping: false });
  });

  it("guarda o access token em memória e o refresh token no storage", () => {
    useAuthStore.getState().setSession({ accessToken: "abc", refreshToken: "xyz" });

    expect(useAuthStore.getState().accessToken).toBe("abc");
    expect(getStoredRefreshToken()).toBe("xyz");
  });

  it("clearSession remove tokens e usuário", () => {
    useAuthStore.getState().setSession({ accessToken: "abc", refreshToken: "xyz" });
    useAuthStore.getState().setUser({
      id: "1",
      email: "a@b.com",
      full_name: "A",
      is_active: true,
      created_at: new Date().toISOString(),
    });

    useAuthStore.getState().clearSession();

    expect(useAuthStore.getState().accessToken).toBeNull();
    expect(useAuthStore.getState().user).toBeNull();
    expect(getStoredRefreshToken()).toBeNull();
  });
});
