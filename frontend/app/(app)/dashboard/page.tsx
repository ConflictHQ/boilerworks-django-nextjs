import { getTranslations } from "next-intl/server";
import { RevenueChart } from "./revenue-chart";
import { SalesChart } from "./sales-chart";
import { ChannelChart } from "./channel-chart";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { TrendingUpIcon, ShoppingCartIcon, UsersIcon, PackageIcon } from "lucide-react";

export default async function DashboardPage() {
  const t = await getTranslations("dashboard");

  const stats = [
    { label: t("stats.revenue"), value: "$48,295", change: "+12.5%", icon: TrendingUpIcon },
    { label: t("stats.orders"), value: "1,284", change: "+8.2%", icon: ShoppingCartIcon },
    { label: t("stats.customers"), value: "3,912", change: "+4.1%", icon: UsersIcon },
    { label: t("stats.products"), value: "248", change: "+2", icon: PackageIcon },
  ];

  return (
    <div className="flex flex-1 flex-col gap-6 p-6">
      {/* stat cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map(({ label, value, change, icon: Icon }) => (
          <Card key={label}>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-muted-foreground text-sm font-medium">{label}</CardTitle>
              <div className="bg-primary/10 text-primary rounded-md p-1.5">
                <Icon className="h-4 w-4" />
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold">{value}</p>
              <p className="mt-1 text-xs text-emerald-600 dark:text-emerald-400">
                {change} {t("stats.fromLastMonth")}
              </p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* charts row */}
      <div className="grid gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>{t("revenue.title")}</CardTitle>
            <CardDescription>{t("revenue.description")}</CardDescription>
          </CardHeader>
          <CardContent>
            <RevenueChart />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>{t("channels.title")}</CardTitle>
            <CardDescription>{t("channels.description")}</CardDescription>
          </CardHeader>
          <CardContent>
            <ChannelChart />
          </CardContent>
        </Card>
      </div>

      {/* sales by category */}
      <Card>
        <CardHeader>
          <CardTitle>{t("sales.title")}</CardTitle>
          <CardDescription>{t("sales.description")}</CardDescription>
        </CardHeader>
        <CardContent>
          <SalesChart />
        </CardContent>
      </Card>
    </div>
  );
}
