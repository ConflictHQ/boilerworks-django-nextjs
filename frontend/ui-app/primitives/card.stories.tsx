import { Button } from "@calliopelabs/ui";
import type { Meta, StoryObj } from "@storybook/nextjs-vite";

import {
  Card,
  CardAction,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "./card";

const meta = { title: "App/Primitives/Card", component: Card } satisfies Meta<typeof Card>;
export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  render: () => (
    <Card className="max-w-sm">
      <CardHeader>
        <CardTitle>Monthly revenue</CardTitle>
        <CardDescription>Last 30 days</CardDescription>
        <CardAction>
          <Button size="sm" variant="outline">
            Export
          </Button>
        </CardAction>
      </CardHeader>
      <CardContent>
        <p className="text-2xl font-semibold">$45,231.89</p>
      </CardContent>
      <CardFooter className="text-muted-foreground text-sm">+20.1% from last month</CardFooter>
    </Card>
  ),
};
