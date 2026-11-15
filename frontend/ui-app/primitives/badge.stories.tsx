import type { Meta, StoryObj } from "@storybook/nextjs-vite";

import { Badge } from "./badge";

/** A label chip for categories and counts. For a status, use the library's StatusBadge. */
const meta = { title: "App/Primitives/Badge", component: Badge } satisfies Meta<typeof Badge>;
export default meta;
type Story = StoryObj<typeof meta>;

export const Variants: Story = {
  render: () => (
    <div className="flex gap-2">
      <Badge>Default</Badge>
      <Badge variant="secondary">Secondary</Badge>
      <Badge variant="outline">Outline</Badge>
      <Badge variant="destructive">Destructive</Badge>
    </div>
  ),
};
