import type { Meta, StoryObj } from "@storybook/nextjs-vite";
import { SearchIcon } from "lucide-react";

import {
  InputGroup,
  InputGroupAddon,
  InputGroupButton,
  InputGroupInput,
  InputGroupText,
} from "./input-group";

/** An input with addons: an icon, a unit, a button. */
const meta = { title: "App/Primitives/InputGroup", component: InputGroup } satisfies Meta<
  typeof InputGroup
>;
export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  render: () => (
    <div className="flex max-w-sm flex-col gap-4">
      <InputGroup>
        <InputGroupAddon>
          <SearchIcon aria-hidden />
        </InputGroupAddon>
        <InputGroupInput placeholder="Search" aria-label="Search" />
      </InputGroup>
      <InputGroup>
        <InputGroupInput placeholder="0.00" aria-label="Amount" />
        <InputGroupAddon align="inline-end">
          <InputGroupText>USD</InputGroupText>
        </InputGroupAddon>
      </InputGroup>
      <InputGroup>
        <InputGroupInput defaultValue="https://example.com" aria-label="URL" />
        <InputGroupAddon align="inline-end">
          <InputGroupButton>Copy</InputGroupButton>
        </InputGroupAddon>
      </InputGroup>
    </div>
  ),
};
