import { cookies } from "next/headers";

export async function fetchToken(): Promise<string | null> {
  try {
    const cookieStore = await cookies();
    return cookieStore.get("backend_jwt")?.value ?? null;
  } catch {
    return null;
  }
}
