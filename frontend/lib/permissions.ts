import { notFound } from "next/navigation";
import { getClient } from "@/lib/apollo";
import { GET_PERMISSION } from "@/graphql/permissions/permissions.queries";
import type {
  PermissionQueryData,
  PermissionQueryVariables,
} from "@/graphql/permissions/permissions.types";
import { PermissionSlug } from "@/graphql/permissions/permissions.types";

export { PermissionSlug };

export async function checkPermission(slug: PermissionSlug): Promise<boolean> {
  try {
    const client = await getClient();
    const { data } = await client.query<PermissionQueryData, PermissionQueryVariables>({
      query: GET_PERMISSION,
      variables: { slug },
    });
    return data?.component?.isActive === true;
  } catch {
    return false;
  }
}

export async function requirePermission(slug: PermissionSlug): Promise<void> {
  const permitted = await checkPermission(slug);
  if (!permitted) {
    notFound();
  }
}
