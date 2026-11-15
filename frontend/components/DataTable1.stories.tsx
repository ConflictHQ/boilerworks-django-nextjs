import type { Meta, StoryObj } from "@storybook/nextjs-vite";

import { DataTable1 } from "./DataTable1";

/** The Table page's product list: in-memory rows on the library DataTable. */
const meta = { title: "App/Screens/Products table", component: DataTable1 } satisfies Meta<
  typeof DataTable1
>;
export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {};
