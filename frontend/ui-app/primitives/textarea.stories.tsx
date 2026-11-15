import type { Meta, StoryObj } from "@storybook/nextjs-vite";

import { Textarea } from "./textarea";

const meta = { title: "App/Primitives/Textarea", component: Textarea } satisfies Meta<
  typeof Textarea
>;
export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: { placeholder: "Write a description", "aria-label": "Description", className: "max-w-sm" },
};
