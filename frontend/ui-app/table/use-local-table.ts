"use client";

import { DEFAULT_PAGE_SIZE, type SortState, type TableController } from "@calliopelabs/ui";
import { useMemo, useState } from "react";

export interface LocalTableOptions<TRow> {
  /** Whether a row matches the search; without it, the search box is hidden. */
  matches?: (row: TRow, query: string) => boolean;
  /** Comparators by sort key; a column with a `sortKey` listed here sorts. */
  comparators?: Record<string, (a: TRow, b: TRow) => number>;
  pageSize?: number;
  pageSizes?: readonly number[];
}

/**
 * A TableController over rows the page already holds in full (fixtures,
 * a small static list). Search, sort and paging apply to the whole set, so
 * every page is right. For data the server pages, use `paginatedController`.
 */
export function useLocalTable<TRow>(
  rows: readonly TRow[],
  { matches, comparators = {}, pageSize: initialPageSize, pageSizes }: LocalTableOptions<TRow> = {}
): TableController<TRow> {
  const [search, setSearchState] = useState("");
  const [sort, setSort] = useState<SortState | undefined>(undefined);
  const [pageIndex, setPageIndex] = useState(0);
  const [pageSize, setPageSizeState] = useState(initialPageSize ?? DEFAULT_PAGE_SIZE);

  const filtered = useMemo(() => {
    const query = search.trim().toLowerCase();
    const found = query && matches ? rows.filter((r) => matches(r, query)) : [...rows];
    const compare = sort && comparators[sort.key];
    if (compare) {
      found.sort((a, b) => (sort.dir === "asc" ? compare(a, b) : compare(b, a)));
    }
    return found;
  }, [rows, search, sort, matches, comparators]);

  const pageCount = Math.max(1, Math.ceil(filtered.length / pageSize));
  const index = Math.min(pageIndex, pageCount - 1);
  const isFiltered = search.trim() !== "";

  return {
    rows: filtered.slice(index * pageSize, (index + 1) * pageSize),
    state: filtered.length > 0 ? "ready" : isFiltered ? "emptyFiltered" : "empty",
    error: null,
    retry: () => {},
    totalCount: filtered.length,
    pageIndex: index,
    hasNext: index < pageCount - 1,
    hasPrev: index > 0,
    next: () => setPageIndex(index + 1),
    prev: () => setPageIndex(index - 1),
    pageSize,
    pageSizes,
    setPageSize: (size) => {
      setPageSizeState(size);
      setPageIndex(0);
    },
    search,
    setSearch: (value) => {
      setSearchState(value);
      setPageIndex(0);
    },
    searchEnabled: Boolean(matches),
    isStale: false,
    sort,
    toggleSort: (key) => {
      setSort((current) =>
        current?.key !== key
          ? { key, dir: "asc" }
          : current.dir === "asc"
            ? { key, dir: "desc" }
            : undefined
      );
      setPageIndex(0);
    },
    sortEnabled: Object.keys(comparators).length > 0,
    isFiltered,
    clearFilters: () => {
      setSearchState("");
      setPageIndex(0);
    },
  };
}
