import { DataTable, StatusBadge, type Column } from "@calliopelabs/ui";
import type { Meta, StoryObj } from "@storybook/nextjs-vite";

import type { PaginatedQueryResult } from "@/hooks/use-paginated-query";

import { paginatedController } from "./paginated-controller";
import { useLocalTable } from "./use-local-table";

type Member = { id: string; name: string; email: string; active: boolean };

const MEMBERS: Member[] = Array.from({ length: 23 }, (_, i) => ({
  id: `m${i + 1}`,
  name: ["Ada Lovelace", "Grace Hopper", "Alan Turing", "Katherine Johnson"][i % 4] + ` ${i + 1}`,
  email: `person${i + 1}@example.com`,
  active: i % 5 !== 0,
}));

const columns: Column<Member>[] = [
  { id: "name", header: "Name", sortKey: "name", cell: (m) => m.name },
  { id: "email", header: "Email", cell: (m) => m.email },
  {
    id: "status",
    header: "Status",
    cell: (m) => (
      <StatusBadge tone={m.active ? "ok" : "muted"}>{m.active ? "Active" : "Inactive"}</StatusBadge>
    ),
  },
];

/** usePaginatedQuery's result, frozen, as the GraphQL hook would return it. */
function result(over: Partial<PaginatedQueryResult<Member>>): PaginatedQueryResult<Member> {
  return {
    nodes: MEMBERS.slice(0, 10),
    totalCount: MEMBERS.length,
    page: 1,
    totalPageCount: 3,
    loading: false,
    error: undefined,
    refetch: () => {},
    goToPage: () => {},
    nextPage: () => {},
    prevPage: () => {},
    perPage: 10,
    setPerPage: () => {},
    search: "",
    setSearch: () => {},
    offset: 1,
    tailOffset: 10,
    filterValues: {},
    setFilter: () => {},
    columnFiltersState: [],
    sorting: [],
    setSorting: () => {},
    onFiltersChange: () => {},
    ...over,
  };
}

function Paginated(props: Partial<PaginatedQueryResult<Member>>) {
  return (
    <DataTable
      label="Members"
      controller={paginatedController(result(props))}
      columns={columns}
      getRowId={(m) => m.id}
      empty={{ title: "No members yet", description: "Invite someone to see them here." }}
    />
  );
}

function Local() {
  const table = useLocalTable(MEMBERS, {
    matches: (m, q) => m.name.toLowerCase().includes(q) || m.email.includes(q),
    comparators: { name: (a, b) => a.name.localeCompare(b.name) },
    pageSize: 10,
  });
  return (
    <DataTable
      label="Members"
      controller={table}
      columns={columns}
      getRowId={(m) => m.id}
      empty={{ title: "No members yet" }}
    />
  );
}

/**
 * The library's DataTable over the app's two controllers: `paginatedController`
 * for a GraphQL list (`usePaginatedQuery`), `useLocalTable` for rows already
 * in hand. Every state the table can be in.
 */
const meta = { title: "App/Tables/Controllers", component: Paginated } satisfies Meta<
  typeof Paginated
>;
export default meta;
type Story = StoryObj<typeof meta>;

export const ServerPaged: Story = {};
export const Loading: Story = { args: { nodes: [], loading: true, totalCount: 0 } };
export const Refreshing: Story = { args: { loading: true } };
export const Empty: Story = { args: { nodes: [], totalCount: 0, totalPageCount: 1 } };
export const NoMatches: Story = {
  args: { nodes: [], totalCount: 0, totalPageCount: 1, search: "zz" },
};
export const Failed: Story = {
  args: { nodes: [], error: new Error("Network error: the API did not answer.") },
};
export const LocalRows: Story = { render: () => <Local /> };
