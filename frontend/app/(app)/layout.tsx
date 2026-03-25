import { redirect } from "next/navigation";
import { cookies } from "next/headers";
import { SidebarInset, SidebarProvider } from "@/components/ui/sidebar";
import { AppSidebar } from "@/components/AppSidebar";
import { PreloadQuery, getClient } from "@/lib/apollo";
import { GET_ME } from "@/graphql/user/user.queries";
import type { CurrentUser, MeQueryData, MeQueryVariables } from "@/graphql/user/user.types";
import { PageHeader } from "@/components/PageHeader";

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
      <SidebarProvider>
        <AppSidebar ssrUser={ssrUser} />
        <SidebarInset>
          <PageHeader />
          {children}
        </SidebarInset>
      </SidebarProvider>
    </PreloadQuery>
  );
}
