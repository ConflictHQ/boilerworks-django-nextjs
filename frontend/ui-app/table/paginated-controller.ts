import type { TableController } from "@calliopelabs/ui";
import type { PaginatedQueryResult } from "@/hooks/use-paginated-query";

/** The page sizes usePaginatedQuery accepts. */
export const PAGINATED_PAGE_SIZES = [5, 10, 20, 50] as const;

/**
 * The library's TableController over the app's `usePaginatedQuery` result:
 * the GraphQL server pages and searches, the DataTable draws. Sorting is off
 * until the query takes a sort argument (`variablesFromSorting`).
 * `isFiltered` is true while a search or a filter narrows the result, so an
 * empty answer reads as "no matches", not "nothing here yet".
 */
export function paginatedController<TRow>(
  result: PaginatedQueryResult<TRow>,
  { searchEnabled = true }: { searchEnabled?: boolean } = {}
): TableController<TRow> {
  const { nodes, loading, error } = result;
  const filterActive = Object.values(result.filterValues).some((v) => v !== undefined && v !== "");
  const isFiltered = result.search.trim() !== "" || filterActive;

  return {
    rows: nodes,
    state: error
      ? "error"
      : loading && nodes.length === 0
        ? "loading"
        : nodes.length === 0
          ? isFiltered
            ? "emptyFiltered"
            : "empty"
          : "ready",
    error: error ? { message: error.message } : null,
    retry: result.refetch,
    totalCount: loading && nodes.length === 0 ? null : result.totalCount,
    pageIndex: result.page - 1,
    hasNext: result.page < result.totalPageCount,
    hasPrev: result.page > 1,
    next: result.nextPage,
    prev: result.prevPage,
    pageSize: result.perPage,
    pageSizes: PAGINATED_PAGE_SIZES,
    setPageSize: result.setPerPage,
    search: result.search,
    setSearch: result.setSearch,
    searchEnabled,
    isStale: loading && nodes.length > 0,
    sort: undefined,
    toggleSort: () => {},
    sortEnabled: false,
    isFiltered,
    clearFilters: () => {
      result.setSearch("");
      for (const key of Object.keys(result.filterValues)) result.setFilter(key, undefined);
    },
  };
}
