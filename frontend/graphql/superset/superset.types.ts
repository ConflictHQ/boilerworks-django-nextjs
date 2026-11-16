export type SupersetDashboard = {
  guid: string;
  embeddedId: string;
  title: string;
  description: string | null;
  order: number;
  supersetDomain: string;
};

export type SupersetDashboardsData = {
  supersetDashboards: SupersetDashboard[];
};

export type SupersetGuestTokenData = {
  supersetGuestToken: {
    ok: boolean;
    token: string | null;
    errors: { field: string; messages: string[] }[];
  };
};
