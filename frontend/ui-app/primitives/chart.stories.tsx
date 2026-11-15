import type { Meta, StoryObj } from "@storybook/nextjs-vite";
import { Bar, BarChart, CartesianGrid, XAxis } from "recharts";

import { ChartContainer, ChartTooltip, ChartTooltipContent, type ChartConfig } from "./chart";

const data = [
  { month: "Jan", sales: 186 },
  { month: "Feb", sales: 305 },
  { month: "Mar", sales: 237 },
  { month: "Apr", sales: 173 },
];

const config = { sales: { label: "Sales", color: "var(--chart-1)" } } satisfies ChartConfig;

/** Recharts on the library's chart tokens (`--chart-1` to `--chart-5`), which follow the accent. */
const meta = { title: "App/Primitives/Chart", component: ChartContainer } satisfies Meta<
  typeof ChartContainer
>;
export default meta;
type Story = StoryObj<typeof meta>;

export const Bars: Story = {
  args: { config, children: <></> },
  render: () => (
    <ChartContainer config={config} className="h-60 w-full max-w-lg">
      <BarChart accessibilityLayer data={data}>
        <CartesianGrid vertical={false} />
        <XAxis dataKey="month" tickLine={false} axisLine={false} />
        <ChartTooltip content={<ChartTooltipContent />} />
        <Bar dataKey="sales" fill="var(--color-sales)" radius={4} />
      </BarChart>
    </ChartContainer>
  ),
};
