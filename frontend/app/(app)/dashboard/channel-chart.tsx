"use client";

import { useTranslations } from "next-intl";
import { Pie, PieChart, Cell } from "recharts";
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
  ChartLegend,
  ChartLegendContent,
  type ChartConfig,
} from "@/components/ui/chart";

const data = [
  { channel: "organic", visitors: 4231 },
  { channel: "direct", visitors: 2847 },
  { channel: "referral", visitors: 1923 },
  { channel: "paid", visitors: 1102 },
];

export const ChannelChart = () => {
  const t = useTranslations("dashboard.channels");
  const config: ChartConfig = {
    organic: { label: t("organic"), color: "var(--color-chart-1)" },
    direct: { label: t("direct"), color: "var(--color-chart-2)" },
    referral: { label: t("referral"), color: "var(--color-chart-3)" },
    paid: { label: t("paid"), color: "var(--color-chart-4)" },
  };
  return (
    <ChartContainer config={config} className="h-[240px] w-full">
      <PieChart>
        <ChartTooltip content={<ChartTooltipContent nameKey="channel" />} />
        <Pie
          data={data}
          dataKey="visitors"
          nameKey="channel"
          innerRadius={60}
          outerRadius={90}
          paddingAngle={3}
        >
          {data.map((entry) => (
            <Cell key={entry.channel} fill={`var(--color-${entry.channel})`} />
          ))}
        </Pie>
        <ChartLegend content={<ChartLegendContent nameKey="channel" />} />
      </PieChart>
    </ChartContainer>
  );
};
