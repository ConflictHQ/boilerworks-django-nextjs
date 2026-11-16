import { PageHeader } from "@calliopelabs/ui";
import { getTranslations } from "next-intl/server";

import { AnalyticsDashboards } from "./analytics-dashboards";

export default async function AnalyticsPage() {
  const t = await getTranslations("analytics");
  return (
    <div className="flex flex-1 flex-col gap-6 p-6">
      <PageHeader title={t("title")} description={t("description")} />
      <AnalyticsDashboards />
    </div>
  );
}
