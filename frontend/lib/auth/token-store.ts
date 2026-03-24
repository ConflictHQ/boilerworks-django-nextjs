const TOKEN_KEY = "jwt";

export async function getClientToken(): Promise<string | null> {
  if (typeof window === "undefined") return null;

  const stored = localStorage.getItem(TOKEN_KEY);
  if (stored && stored !== "undefined" && stored !== "null") return stored;

  try {
    const res = await fetch("/api/session/getToken", { method: "POST" });
    if (!res.ok) return null;
    const data = await res.json();
    const token: string | null = data.Authorization ?? null;
    if (token) localStorage.setItem(TOKEN_KEY, token);
    return token;
  } catch {
    return null;
  }
}

export function clearToken(): void {
  localStorage.removeItem(TOKEN_KEY);
}
