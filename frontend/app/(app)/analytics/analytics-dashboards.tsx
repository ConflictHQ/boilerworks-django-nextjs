"use client";

import { EmptyState, ErrorState, LoadingState } from "@calliopelabs/ui";
import { BarChart3Icon } from "lucide-react";
import { useTranslations } from "next-intl";

import { useSupersetDashboards, useSupersetGuestToken } from "@/graphql/superset/superset.hooks";
import type { SupersetDashboard as Dashboard } from "@/graphql/superset/superset.types";
import { SupersetDashboard } from "@/ui-app/analytics/SupersetDashboard";

function DashboardEmbed({ dashboard }: { dashboard: Dashboard }) {
  const fetchGuestToken = useSupersetGuestToken(dashboard.guid);
  return (
    <section className="flex flex-col gap-2">
      <h2 className="text-lg font-semibold">{dashboard.title}</h2>
      {dashboard.description && (
        <p className="text-muted-foreground text-sm">{dashboard.description}</p>
      )}
      <SupersetDashboard
        embeddedId={dashboard.embeddedId}
        supersetDomain={dashboard.supersetDomain}
        title={dashboard.title}
        fetchGuestToken={fetchGuestToken}
      />
    </section>
  );
}

export function AnalyticsDashboards() {
  const t = useTranslations("analytics");
  const { dashboards, loading, error, refetch } = useSupersetDashboards();

  if (loading && dashboards.length === 0) return <LoadingState label={t("loadingList")} />;
  if (error)
    return (
      <ErrorState
        title={t("listFailed")}
        error={error}
        onRetry={() => refetch()}
        retryLabel={t("retry")}
      />
    );
  if (dashboards.length === 0)
    return (
      <EmptyState
        icon={<BarChart3Icon aria-hidden />}
        title={t("emptyTitle")}
        description={t("emptyDescription")}
      />
    );

  return (
    <div className="flex flex-col gap-8">
      {dashboards.map((dashboard) => (
        <DashboardEmbed key={dashboard.guid} dashboard={dashboard} />
      ))}
    </div>
  );
}
