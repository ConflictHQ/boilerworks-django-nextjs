"use client";

import { useQuery } from "@apollo/client/react";
import { GET_PERMISSION } from "./permissions.queries";
import type { PermissionQueryData, PermissionQueryVariables } from "./permissions.types";

export const usePermission = (slug: string) => {
  const { data, loading, error } = useQuery<PermissionQueryData, PermissionQueryVariables>(
    GET_PERMISSION,
    {
      variables: { slug },
      fetchPolicy: "cache-first",
    }
  );

  return {
    data,
    component: data?.component ?? null,
    isActive: data?.component?.isActive ?? false,
    loading,
    error,
  };
};
