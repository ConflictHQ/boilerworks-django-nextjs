"use client";

import { type ColumnDef } from "@tanstack/react-table";
import { DataTableColumnHeader } from "@/components/data-table";
import type { FilterConfig } from "@/components/data-table/types";
import { usePaginatedQuery } from "@/hooks/use-paginated-query";
import { getEmployees } from "./employees.queries";
import type {
  Employee,
  EmployeeEdge,
  EmployeesQueryData,
  EmployeesQueryVariables,
} from "./employees.types";

// ─── columns ──────────────────────────────────────────────────────────────────

export const employeeColumns: ColumnDef<Employee, unknown>[] = [
  {
    id: "name",
    accessorFn: (row) =>
      row.user.profile?.displayName ?? `${row.user.firstName} ${row.user.lastName}`,
    header: ({ column }) => <DataTableColumnHeader column={column} title="Name" />,
    cell: ({ getValue }) => <div className="font-medium">{getValue() as string}</div>,
    enableSorting: true,
  },
  {
    id: "email",
    accessorFn: (row) => row.user.email,
    header: ({ column }) => <DataTableColumnHeader column={column} title="Email" />,
    enableSorting: true,
  },
  {
    id: "status",
    accessorFn: (row) => row.user.isActive,
    header: ({ column }) => <DataTableColumnHeader column={column} title="Status" />,
    cell: ({ getValue }) => ((getValue() as boolean) ? "Active" : "Inactive"),
    enableSorting: false,
  },
];

// ─── filter config ────────────────────────────────────────────────────────────

export const employeeFilters: FilterConfig[] = [
  {
    id: "status",
    label: "Status",
    type: "select",
    options: [
      { value: "active", label: "Active" },
      { value: "deactivated", label: "Deactivated" },
    ],
  },
];

// ─── status filter ────────────────────────────────────────────────────────────

type EmployeeStatus = "active" | "deactivated" | undefined;

function parseStatus(val: string | undefined): EmployeeStatus {
  if (val === "active" || val === "deactivated") return val;
  return undefined;
}

function statusToShowDeactivated(status: EmployeeStatus): boolean | undefined {
  if (status === "active") return false;
  if (status === "deactivated") return true;
  return undefined; // "all" — omitted by stripNullish, API uses its default
}

// ─── hook ─────────────────────────────────────────────────────────────────────

export const useEmployees = (perPage?: number) => {
  const result = usePaginatedQuery<
    EmployeesQueryVariables,
    EmployeesQueryData,
    EmployeeEdge,
    Employee
  >({
    query: getEmployees,
    variables: {},
    ancestor: "employees",
    dataExtractor: (edges) => edges.map((e) => e.node),
    perPage,
    storageKey: "employees-per-page",
    fetchPolicy: "cache-and-network",
    urlSync: "employee",
    filterKeys: ["status"],
    variablesFromFilters: (filters) => ({
      showDeactivated: statusToShowDeactivated(parseStatus(filters.status)),
    }),
  });

  const status = parseStatus(result.filterValues.status);
  const setStatus = (val: string | undefined) => result.setFilter("status", val);

  return { ...result, status, setStatus };
};
