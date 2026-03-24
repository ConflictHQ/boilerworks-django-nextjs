"use client";

import { useTranslations } from "next-intl";
import { Bar, BarChart, CartesianGrid, XAxis, YAxis } from "recharts";
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
  type ChartConfig,
} from "@/components/ui/chart";

export const SalesChart = () => {
  const t = useTranslations("dashboard.sales");

  const data = [
    { category: t("electronics"), units: 412 },
    { category: t("clothing"), units: 298 },
    { category: t("accessories"), units: 341 },
    { category: t("footwear"), units: 187 },
    { category: t("sports"), units: 156 },
  ];

  const config: ChartConfig = {
    units: { label: t("label"), color: "var(--color-chart-1)" },
  };

  return (
    <ChartContainer config={config} className="h-[200px] w-full">
      <BarChart data={data} margin={{ left: 0, right: 0 }}>
        <CartesianGrid vertical={false} strokeDasharray="3 3" />
        <XAxis dataKey="category" tickLine={false} axisLine={false} tick={{ fontSize: 12 }} />
        <YAxis tickLine={false} axisLine={false} tick={{ fontSize: 12 }} />
        <ChartTooltip content={<ChartTooltipContent />} />
        <Bar dataKey="units" fill="var(--color-units)" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ChartContainer>
  );
};
