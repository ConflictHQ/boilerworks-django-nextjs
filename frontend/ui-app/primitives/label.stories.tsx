import { Checkbox } from "@calliopelabs/ui";
import type { Meta, StoryObj } from "@storybook/nextjs-vite";

import { Label } from "./label";

const meta = { title: "App/Primitives/Label", component: Label } satisfies Meta<typeof Label>;
export default meta;
type Story = StoryObj<typeof meta>;

export const WithCheckbox: Story = {
  render: () => (
    <div className="flex items-center gap-2">
      <Checkbox id="terms" />
      <Label htmlFor="terms">Accept the terms</Label>
    </div>
  ),
};
