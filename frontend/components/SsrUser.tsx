import { getClient } from "@/lib/apollo";
import { GET_ME } from "@/graphql/user/user.queries";
import { Badge } from "@/components/ui/badge";
import type { MeQueryData } from "@/graphql/user/user.types";

export default async function SsrUser() {
  let label: string | undefined;
  try {
    const client = await getClient();
    const { data } = await client.query<MeQueryData>({ query: GET_ME });
    label = data?.me?.profile?.username ?? data?.me?.id;
  } catch (e) {
    label = e instanceof Error ? e.message : String(e);
  }
  return <Badge variant="secondary">SSR: {label}</Badge>;
}
