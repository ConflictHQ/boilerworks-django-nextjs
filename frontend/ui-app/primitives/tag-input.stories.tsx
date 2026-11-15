import type { Meta, StoryObj } from "@storybook/nextjs-vite";
import { useState } from "react";

import { TagInput } from "./tag-input";

const meta = { title: "App/Primitives/TagInput", component: TagInput } satisfies Meta<
  typeof TagInput
>;
export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: { value: [], onChange: () => {} },
  render: function Render() {
    const [tags, setTags] = useState(["design", "ops"]);
    return (
      <div className="max-w-sm">
        <TagInput
          value={tags}
          onChange={setTags}
          suggestions={["design", "ops", "backend", "frontend"]}
          placeholder="Add a tag"
        />
      </div>
    );
  },
};
