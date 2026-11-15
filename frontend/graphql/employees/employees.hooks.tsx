"use client";

import { StatusBadge, type Column } from "@calliopelabs/ui";
import { usePaginatedQuery } from "@/hooks/use-paginated-query";
import { getEmployees } from "./employees.queries";
import type {
  Employee,
  EmployeeEdge,
  EmployeesQueryData,
  EmployeesQueryVariables,
} from "./employees.types";

// ─── columns ──────────────────────────────────────────────────────────────────

export const employeeColumns: Column<Employee>[] = [
  {
    id: "name",
    header: "Name",
    cell: (row) => (
      <span className="font-medium">
        {row.user.profile?.displayName ?? `${row.user.firstName} ${row.user.lastName}`}
      </span>
    ),
  },
  { id: "email", header: "Email", cell: (row) => row.user.email },
  {
    id: "status",
    header: "Status",
    cell: (row) => (
      <StatusBadge tone={row.user.isActive ? "ok" : "muted"}>
        {row.user.isActive ? "Active" : "Inactive"}
      </StatusBadge>
    ),
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
