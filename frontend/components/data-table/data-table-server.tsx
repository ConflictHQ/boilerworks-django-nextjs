"use client";

import * as React from "react";
import {
  type ColumnDef,
  type ColumnFiltersState,
  flexRender,
  getCoreRowModel,
  getSortedRowModel,
  type SortingState,
  useReactTable,
} from "@tanstack/react-table";
import type { ErrorLike } from "@apollo/client";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { type FilterConfig } from "./types";
import { DataTableToolbar } from "./data-table-toolbar";

// ─── constants ────────────────────────────────────────────────────────────────

const PAGE_SIZES = [5, 10, 20, 50];

// ─── types ────────────────────────────────────────────────────────────────────

type DataTableServerProps<TData> = {
  data: TData[];
  columns: ColumnDef<TData, unknown>[];
  getRowId?: (row: TData) => string;
  loading?: boolean;
  error?: ErrorLike;
  totalCount: number;
  page: number;
  totalPageCount: number;
  perPage: number;
  onPerPageChange: (n: number) => void;
  onNextPage: () => void;
  onPrevPage: () => void;
  onGoToPage: (p: number) => void;
  onSearchChange?: (s: string) => void;
  /** Called with the new column-filters state whenever the filter panel applies changes.
   *  Use this to map filter values back to server-side query variables. */
  onFiltersChange?: (filters: ColumnFiltersState) => void;
  /** Called with the new sort state whenever the user clicks a column header. */
  onSortingChange?: (sorting: SortingState) => void;
  filters?: FilterConfig[];
  /** Initial column-filter state — use to restore filters from URL on mount. */
  initialColumnFilters?: ColumnFiltersState;
  /** Initial sort state — use to restore sort from URL on mount. */
  initialSorting?: SortingState;
  searchPlaceholder?: string;
  toolbarExtra?: React.ReactNode;
  offset: number;
  tailOffset: number;
};

// ─── component ────────────────────────────────────────────────────────────────

export const DataTableServer = <TData,>({
  data,
  columns,
  getRowId,
  loading = false,
  error,
  totalCount,
  page,
  totalPageCount,
  perPage,
  onPerPageChange,
  onNextPage,
  onPrevPage,
  onGoToPage: _,
  onSearchChange,
  onFiltersChange,
  onSortingChange,
  filters = [],
  initialColumnFilters,
  initialSorting,
  searchPlaceholder,
  toolbarExtra,
  offset,
  tailOffset,
}: DataTableServerProps<TData>) => {
  const [sorting, setSorting] = React.useState<SortingState>(initialSorting ?? []);
  const [globalFilter, setGlobalFilter] = React.useState("");
  const [columnFilters, setColumnFilters] = React.useState<ColumnFiltersState>(
    initialColumnFilters ?? []
  );

  const handleGlobalFilterChange = (value: string) => {
    setGlobalFilter(value);
    onSearchChange?.(value);
  };

  const handleColumnFiltersChange = (
    updater: ColumnFiltersState | ((prev: ColumnFiltersState) => ColumnFiltersState)
  ) => {
    const next = typeof updater === "function" ? updater(columnFilters) : updater;
    setColumnFilters(next);
    onFiltersChange?.(next);
  };

  const handleSortingChange = (updater: SortingState | ((prev: SortingState) => SortingState)) => {
    const next = typeof updater === "function" ? updater(sorting) : updater;
    setSorting(next);
    onSortingChange?.(next);
  };

  const table = useReactTable({
    data,
    columns,
    getRowId,
    pageCount: totalPageCount,
    state: {
      sorting,
      pagination: { pageIndex: page - 1, pageSize: perPage },
      globalFilter,
      columnFilters,
    },
    manualPagination: true,
    manualSorting: true,
    manualFiltering: true,
    onSortingChange: handleSortingChange,
    onGlobalFilterChange: handleGlobalFilterChange,
    onColumnFiltersChange: handleColumnFiltersChange,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
  });

  const canPrev = page > 1;
  const canNext = page < totalPageCount;

  const countLabel = totalCount === 0 ? "0 results" : `${offset}–${tailOffset} of ${totalCount}`;

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-start gap-2">
        <div className="flex-1">
          <DataTableToolbar table={table} filters={filters} searchPlaceholder={searchPlaceholder} />
        </div>
        {toolbarExtra}
      </div>

      {error && <p className="text-destructive text-sm">{error.message}</p>}

      <div className="overflow-hidden rounded-md border">
        <Table>
          <TableHeader>
            {table.getHeaderGroups().map((headerGroup) => (
              <TableRow key={headerGroup.id}>
                {headerGroup.headers.map((header) => (
                  <TableHead key={header.id} className="px-0">
                    {header.isPlaceholder
                      ? null
                      : flexRender(header.column.columnDef.header, header.getContext())}
                  </TableHead>
                ))}
              </TableRow>
            ))}
          </TableHeader>
          <TableBody className={loading ? "opacity-50 transition-opacity" : "transition-opacity"}>
            {table.getRowModel().rows?.length
              ? table.getRowModel().rows.map((row) => (
                  <TableRow key={row.id} data-state={row.getIsSelected() && "selected"}>
                    {row.getVisibleCells().map((cell) => (
                      <TableCell key={cell.id}>
                        {flexRender(cell.column.columnDef.cell, cell.getContext())}
                      </TableCell>
                    ))}
                  </TableRow>
                ))
              : !loading && (
                  <TableRow>
                    <TableCell colSpan={columns.length} className="h-24 text-center">
                      No results.
                    </TableCell>
                  </TableRow>
                )}
          </TableBody>
        </Table>
      </div>

      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <p className="text-muted-foreground text-sm">Rows per page</p>
          <Select value={String(perPage)} onValueChange={(v) => onPerPageChange(Number(v))}>
            <SelectTrigger className="h-8 w-16">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {PAGE_SIZES.map((size) => (
                <SelectItem key={size} value={String(size)}>
                  {size}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <p className="text-muted-foreground text-sm">{countLabel}</p>
        </div>

        <div className="flex items-center gap-1">
          <p className="text-muted-foreground mr-2 text-sm">
            Page {page} of {totalPageCount}
          </p>
          <Button variant="outline" size="icon" onClick={onPrevPage} disabled={!canPrev}>
            <ChevronLeft className="h-4 w-4" />
          </Button>
          <Button variant="outline" size="icon" onClick={onNextPage} disabled={!canNext}>
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  );
};
