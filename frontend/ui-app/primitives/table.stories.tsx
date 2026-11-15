import type { Meta, StoryObj } from "@storybook/nextjs-vite";

import {
  Table,
  TableBody,
  TableCaption,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "./table";

/** A plain static table. For lists of records, use the library's DataTable. */
const meta = { title: "App/Primitives/Table", component: Table } satisfies Meta<typeof Table>;
export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  render: () => (
    <Table>
      <TableCaption>Plans</TableCaption>
      <TableHeader>
        <TableRow>
          <TableHead>Plan</TableHead>
          <TableHead className="text-right">Seats</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        <TableRow>
          <TableCell>Team</TableCell>
          <TableCell className="text-right">10</TableCell>
        </TableRow>
        <TableRow>
          <TableCell>Enterprise</TableCell>
          <TableCell className="text-right">Unlimited</TableCell>
        </TableRow>
      </TableBody>
    </Table>
  ),
};
