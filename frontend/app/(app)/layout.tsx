import { redirect } from "next/navigation";
import { cookies } from "next/headers";
import { AppChrome } from "@/components/AppChrome";
import { PreloadQuery, getClient } from "@/lib/apollo";
import { GET_ME } from "@/graphql/user/user.queries";
import type { CurrentUser, MeQueryData, MeQueryVariables } from "@/graphql/user/user.types";

export default async function AppLayout({ children }: { children: React.ReactNode }) {
  // Check for auth token in cookies — if no token at all, redirect to login
  const cookieStore = await cookies();
  const hasToken = cookieStore.has("backend_jwt") || cookieStore.has("sessionid");

  if (!hasToken) {
    redirect("/auth/login");
  }

  let ssrUser: CurrentUser | null = null;

  try {
    const client = await getClient();
    const { data } = await client.query<MeQueryData, MeQueryVariables>({ query: GET_ME });
    ssrUser = data?.me ?? null;
  } catch {
    // network error or invalid token — don't redirect here,
    // let client-side Apollo errorLink handle UNAUTHENTICATED
  }

  return (
    <PreloadQuery query={GET_ME}>
      <AppChrome ssrUser={ssrUser}>{children}</AppChrome>
    </PreloadQuery>
  );
}
