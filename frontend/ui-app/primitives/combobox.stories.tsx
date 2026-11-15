import type { Meta, StoryObj } from "@storybook/nextjs-vite";

import {
  Combobox,
  ComboboxContent,
  ComboboxEmpty,
  ComboboxInput,
  ComboboxItem,
  ComboboxList,
} from "./combobox";

const frameworks = ["Next.js", "NestJS", "Django", "FastAPI", "Rails"];

/** A searchable select (Base UI). */
const meta = { title: "App/Primitives/Combobox", component: Combobox } satisfies Meta<
  typeof Combobox
>;
export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  render: () => (
    <div className="max-w-xs">
      <Combobox items={frameworks}>
        <ComboboxInput placeholder="Pick a framework" aria-label="Framework" />
        <ComboboxContent>
          <ComboboxEmpty>No framework found.</ComboboxEmpty>
          <ComboboxList>
            {(item: string) => (
              <ComboboxItem key={item} value={item}>
                {item}
              </ComboboxItem>
            )}
          </ComboboxList>
        </ComboboxContent>
      </Combobox>
    </div>
  ),
};
