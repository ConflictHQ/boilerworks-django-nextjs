"use client";

import { useEffect } from "react";
import { notFound, useRouter } from "next/navigation";
import { Loader2Icon } from "lucide-react";
import { useMe } from "@/graphql/user/user.hooks";
import { usePermission } from "@/graphql/permissions/permissions.hooks";
import { clearToken } from "@/lib/auth/token-store";

type PermissionGuardProps = {
  permission: string;
  children: React.ReactNode;
};

export function PermissionGuard({ permission, children }: PermissionGuardProps) {
  const router = useRouter();
  const { user, loading: meLoading } = useMe();
  const { component, loading: permLoading } = usePermission(permission);

  useEffect(() => {
    if (!meLoading && user === null) {
      clearToken();
      router.replace("/auth/logout");
    }
  }, [meLoading, user, router]);

  if (meLoading || permLoading) {
    return (
      <div className="flex flex-1 items-center justify-center p-6">
        <Loader2Icon className="text-muted-foreground h-6 w-6 animate-spin" />
      </div>
    );
  }

  if (component?.isActive === false) {
    notFound();
  }

  return <>{children}</>;
}

export function withPermissionAuthenticationRequired<T extends object>(
  WrappedComponent: React.ComponentType<T>,
  permission: string
): React.FC<T> {
  const GuardedComponent: React.FC<T> = (props: T) => (
    <PermissionGuard permission={permission}>
      <WrappedComponent {...props} />
    </PermissionGuard>
  );
  GuardedComponent.displayName = `withPermissionAuthenticationRequired(${WrappedComponent.displayName ?? WrappedComponent.name ?? "Component"})`;
  return GuardedComponent;
}
