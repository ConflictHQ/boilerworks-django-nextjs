import { useMutation, useQuery } from "@apollo/client/react";
import * as React from "react";

import { SUPERSET_GUEST_TOKEN } from "./superset.mutations";
import { GET_SUPERSET_DASHBOARDS } from "./superset.queries";
import type { SupersetDashboardsData, SupersetGuestTokenData } from "./superset.types";

export const useSupersetDashboards = () => {
  const { data, loading, error, refetch } = useQuery<SupersetDashboardsData>(
    GET_SUPERSET_DASHBOARDS,
    { fetchPolicy: "cache-and-network" }
  );
  return { dashboards: data?.supersetDashboards ?? [], loading, error, refetch };
};

/** A fetchGuestToken for the embed: asks the backend for a guest token for one dashboard. */
export const useSupersetGuestToken = (dashboardGuid: string) => {
  const [issue] = useMutation<SupersetGuestTokenData>(SUPERSET_GUEST_TOKEN);
  return React.useCallback(async () => {
    const { data } = await issue({ variables: { dashboard: dashboardGuid } });
    const result = data?.supersetGuestToken;
    if (!result?.ok || !result.token) {
      throw new Error(result?.errors[0]?.messages[0] ?? "No guest token was issued.");
    }
    return result.token;
  }, [issue, dashboardGuid]);
};
