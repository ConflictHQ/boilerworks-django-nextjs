"use client";

import { DataTable } from "@calliopelabs/ui";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/ui-app/primitives/select";
import { employeeColumns, useEmployees } from "@/graphql/employees/employees.hooks";
import { paginatedController } from "@/ui-app/table/paginated-controller";

/** A server-paged table: GraphQL pages and searches, the library DataTable draws. */
export function DataTableEmployees() {
  const employees = useEmployees();

  return (
    <DataTable
      label="Employees"
      controller={paginatedController(employees)}
      columns={employeeColumns}
      getRowId={(row) => row.id}
      searchPlaceholder="Search employees…"
      empty={{ title: "No employees yet", description: "Invite someone to see them here." }}
      toolbar={
        <Select
          value={employees.status ?? "all"}
          onValueChange={(v) => employees.setStatus(v === "all" ? undefined : v)}
        >
          <SelectTrigger className="w-40" aria-label="Status">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All statuses</SelectItem>
            <SelectItem value="active">Active</SelectItem>
            <SelectItem value="deactivated">Deactivated</SelectItem>
          </SelectContent>
        </Select>
      }
    />
  );
}
