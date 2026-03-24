"use client";

import { DataTableServer } from "@/components/data-table";
import {
  employeeColumns,
  employeeFilters,
  useEmployees,
} from "@/graphql/employees/employees.hooks";

// ─── component ────────────────────────────────────────────────────────────────

export function DataTableEmployees() {
  const {
    nodes,
    loading,
    error,
    totalCount,
    page,
    totalPageCount,
    perPage,
    setPerPage,
    nextPage,
    prevPage,
    goToPage,
    setSearch,
    offset,
    tailOffset,
    onFiltersChange,
    columnFiltersState,
    sorting,
    setSorting,
  } = useEmployees();

  return (
    <DataTableServer
      data={nodes}
      columns={employeeColumns}
      getRowId={(row) => row.id}
      loading={loading}
      error={error}
      totalCount={totalCount}
      page={page}
      totalPageCount={totalPageCount}
      perPage={perPage}
      onPerPageChange={setPerPage}
      onNextPage={nextPage}
      onPrevPage={prevPage}
      onGoToPage={goToPage}
      onSearchChange={setSearch}
      onFiltersChange={onFiltersChange}
      onSortingChange={setSorting}
      filters={employeeFilters}
      initialColumnFilters={columnFiltersState}
      initialSorting={sorting}
      searchPlaceholder="Search employees…"
      offset={offset}
      tailOffset={tailOffset}
    />
  );
}
