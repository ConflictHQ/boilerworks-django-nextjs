import type { Meta, StoryObj } from "@storybook/nextjs-vite";

import { Separator } from "./separator";

const meta = { title: "App/Primitives/Separator", component: Separator } satisfies Meta<
  typeof Separator
>;
export default meta;
type Story = StoryObj<typeof meta>;

export const Horizontal: Story = {
  render: () => (
    <div className="max-w-sm text-sm">
      <p>Above</p>
      <Separator className="my-3" />
      <p>Below</p>
    </div>
  ),
};

export const Vertical: Story = {
  render: () => (
    <div className="flex h-5 items-center gap-3 text-sm">
      <span>Docs</span>
      <Separator orientation="vertical" />
      <span>API</span>
    </div>
  ),
};
