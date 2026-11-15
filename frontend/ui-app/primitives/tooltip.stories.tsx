import { Button } from "@calliopelabs/ui";
import type { Meta, StoryObj } from "@storybook/nextjs-vite";

import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "./tooltip";

const meta = { title: "App/Primitives/Tooltip", component: Tooltip } satisfies Meta<typeof Tooltip>;
export default meta;
type Story = StoryObj<typeof meta>;

export const Open: Story = {
  render: () => (
    <TooltipProvider>
      <Tooltip defaultOpen>
        <TooltipTrigger asChild>
          <Button variant="outline">Hover me</Button>
        </TooltipTrigger>
        <TooltipContent>Copies the link</TooltipContent>
      </Tooltip>
    </TooltipProvider>
  ),
};
