/**
 * Auth client — token storage, login, refresh, logout.
 *
 * Storage strategy: access token in memory (module-level variable) +
 * refresh token in localStorage. This avoids XSS exfiltration of the
 * access token while keeping the refresh token persistent across page loads.
 *
 * In a production deployment with a dedicated BFF (Next.js API routes),
 * the refresh token would move to an httpOnly cookie. That refactor is a
 * drop-in: swap the localStorage calls for fetch("/api/auth/...") calls.
 */

const API_BASE = process.env["NEXT_PUBLIC_API_URL"] ?? "http://localhost:8000";

const ACCESS_TOKEN_KEY = "forense_access_token";
const REFRESH_TOKEN_KEY = "forense_refresh_token";

// ── In-memory access token ────────────────────────────────────────────────────

let _accessToken: string | null = null;

export function getAccessToken(): string | null {
  if (_accessToken) return _accessToken;
  // Attempt rehydration from sessionStorage (survives page refresh within tab)
  if (typeof window !== "undefined") {
    _accessToken = sessionStorage.getItem(ACCESS_TOKEN_KEY);
  }
  return _accessToken;
}

function setAccessToken(token: string): void {
  _accessToken = token;
  if (typeof window !== "undefined") {
    sessionStorage.setItem(ACCESS_TOKEN_KEY, token);
  }
}

function clearAccessToken(): void {
  _accessToken = null;
  if (typeof window !== "undefined") {
    sessionStorage.removeItem(ACCESS_TOKEN_KEY);
  }
}

function setRefreshToken(token: string): void {
  if (typeof window !== "undefined") {
    localStorage.setItem(REFRESH_TOKEN_KEY, token);
  }
}

function getRefreshToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(REFRESH_TOKEN_KEY);
}

function clearRefreshToken(): void {
  if (typeof window !== "undefined") {
    localStorage.removeItem(REFRESH_TOKEN_KEY);
  }
}

// ── HTTP helpers ──────────────────────────────────────────────────────────────

class AuthError extends Error {
  constructor(
    public readonly status: number,
    public readonly detail: string,
  ) {
    super(`Auth ${status}: ${detail}`);
    this.name = "AuthError";
  }
}

async function authFetch<T>(
  path: string,
  init: RequestInit = {},
  withAuth = true,
): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(init.headers as Record<string, string> ?? {}),
  };

  if (withAuth) {
    const token = getAccessToken();
    if (token) headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}${path}`, { ...init, headers });

  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = (await res.json()) as { detail?: string };
      detail = body.detail ?? detail;
    } catch {
      // ignore
    }
    throw new AuthError(res.status, detail);
  }

  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

// ── Public API ────────────────────────────────────────────────────────────────

export interface LoginResult {
  access_token?: string;
  refresh_token?: string;
  requires_mfa?: boolean;
  requires_mfa_setup?: boolean;
  mfa_pending_token?: string;
}

export async function login(email: string, password: string): Promise<LoginResult> {
  const result = await authFetch<LoginResult>(
    "/api/v1/auth/login",
    { method: "POST", body: JSON.stringify({ email, password }) },
    false,
  );

  if (result.access_token && result.refresh_token) {
    setAccessToken(result.access_token);
    setRefreshToken(result.refresh_token);
  }

  return result;
}

export async function verifyMfa(
  mfaToken: string,
  totpCode: string,
): Promise<void> {
  const result = await authFetch<{ access_token: string; refresh_token: string }>(
    "/api/v1/auth/mfa/verify",
    {
      method: "POST",
      body: JSON.stringify({ mfa_token: mfaToken, totp_code: totpCode }),
    },
    false,
  );
  setAccessToken(result.access_token);
  setRefreshToken(result.refresh_token);
}

export async function refreshAccessToken(): Promise<boolean> {
  const refreshToken = getRefreshToken();
  if (!refreshToken) return false;

  try {
    const result = await authFetch<{ access_token: string; refresh_token: string }>(
      "/api/v1/auth/refresh",
      { method: "POST", body: JSON.stringify({ refresh_token: refreshToken }) },
      false,
    );
    setAccessToken(result.access_token);
    setRefreshToken(result.refresh_token);
    return true;
  } catch {
    clearAccessToken();
    clearRefreshToken();
    return false;
  }
}

export async function logout(): Promise<void> {
  const refreshToken = getRefreshToken();
  const accessToken = getAccessToken();
  if (accessToken && refreshToken) {
    try {
      await authFetch(
        "/api/v1/auth/logout",
        { method: "POST", body: JSON.stringify({ refresh_token: refreshToken }) },
      );
    } catch {
      // Swallow — we clear local state regardless
    }
  }
  clearAccessToken();
  clearRefreshToken();
}

export function isAuthenticated(): boolean {
  return getAccessToken() !== null;
}

export { AuthError };
