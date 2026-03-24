"use client";

import { withPermissionAuthenticationRequired } from "@/components/PermissionGuard";
import { PermissionSlug } from "@/graphql/permissions/permissions.types";

function SecuredContent() {
  return (
    <div className="bg-muted/50 rounded-lg border p-4">
      <p className="text-sm">
        This content was rendered by a client component guarded with{" "}
        <code className="font-mono">withPermissionAuthenticationRequired</code>. If the{" "}
        <code className="font-mono">secured-page</code> permission were inactive, this would show a
        404 instead.
      </p>
    </div>
  );
}

export const SecuredClientSection = withPermissionAuthenticationRequired(
  SecuredContent,
  PermissionSlug.SecuredPage
);
