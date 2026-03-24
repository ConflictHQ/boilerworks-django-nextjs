"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { useQuery } from "@apollo/client/react";
import type {
  DocumentNode,
  ErrorLike,
  ErrorPolicy,
  OperationVariables,
  WatchQueryFetchPolicy,
} from "@apollo/client";
import type { ColumnFiltersState, SortingState } from "@tanstack/react-table";
import { useDebounce } from "@/hooks/use-debounce";
import { useLocalStorage } from "@/hooks/use-local-storage";

// ─── helpers ──────────────────────────────────────────────────────────────────

const PAGE_SIZES = [5, 10, 20, 50];
const DEFAULT_PER_PAGE = 10;

function sanitizePerPage(value: number): number {
  if (PAGE_SIZES.includes(value)) return value;
  return DEFAULT_PER_PAGE;
}

function sanitizePage(page: number, totalPageCount: number): number {
  if (page < 1) return 1;
  if (totalPageCount > 0 && page > totalPageCount) return totalPageCount;
  return page;
}

function stripNullish(obj: Record<string, unknown>): Record<string, unknown> {
  return Object.fromEntries(Object.entries(obj).filter(([, v]) => v !== null && v !== undefined));
}

// ─── types ────────────────────────────────────────────────────────────────────

type PaginatedQueryOptions<TVariables extends OperationVariables, TItem, TExtractedData> = {
  query: DocumentNode;
  variables: Partial<TVariables>;
  dataExtractor: (items: TItem[]) => TExtractedData[];
  ancestor: string;
  perPage?: number;
  storageKey?: string;
  shouldSkip?: boolean;
  fetchPolicy?: WatchQueryFetchPolicy;
  errorPolicy?: ErrorPolicy;
  /** Sync page, search, perPage, filters, and sort to URL query params.
   *  Pass true to use default keys, or a string prefix (e.g. "emp" → ?emp-page=2).
   *  Wrap the consumer in <Suspense> when urlSync is enabled. */
  urlSync?: boolean | string;
  /** Filter column IDs to track in URL (e.g. ["status", "type"]).
   *  Synced as ?${prefix}filter-${id}=value. Requires urlSync. */
  filterKeys?: string[];
  /** Map current filter values to query variables. */
  variablesFromFilters?: (filters: Record<string, string | undefined>) => Partial<TVariables>;
  /** Map current sort state to query variables. */
  variablesFromSorting?: (sorting: SortingState) => Partial<TVariables>;
};

export type PaginatedQueryResult<TExtractedData> = {
  nodes: TExtractedData[];
  totalCount: number;
  page: number;
  totalPageCount: number;
  loading: boolean;
  error: ErrorLike | undefined;
  refetch: () => void;
  goToPage: (p: number) => void;
  nextPage: () => void;
  prevPage: () => void;
  perPage: number;
  setPerPage: (n: number) => void;
  search: string;
  setSearch: (s: string) => void;
  offset: number;
  tailOffset: number;
  /** Current filter values keyed by filter ID. */
  filterValues: Record<string, string | undefined>;
  /** Set or clear a single filter. Resets page to 1. */
  setFilter: (id: string, value: string | undefined) => void;
  /** Derived ColumnFiltersState for initialising a TanStack table. */
  columnFiltersState: ColumnFiltersState;
  /** Current sort state. */
  sorting: SortingState;
  /** Update sort state (synced to URL if urlSync is enabled). */
  setSorting: (sorting: SortingState) => void;
  /** Drop-in handler for DataTableServer's onFiltersChange prop.
   *  Syncs all filterKeys to URL and query variables automatically. */
  onFiltersChange: (filters: ColumnFiltersState) => void;
};

// ─── hook ─────────────────────────────────────────────────────────────────────

export function usePaginatedQuery<
  TVariables extends OperationVariables,
  TData,
  TItem,
  TExtractedData,
>({
  query,
  variables,
  dataExtractor,
  ancestor,
  perPage: initialPerPage,
  storageKey = "paginated-query-per-page",
  shouldSkip = false,
  fetchPolicy,
  errorPolicy,
  urlSync = false,
  filterKeys = [],
  variablesFromFilters,
  variablesFromSorting,
}: PaginatedQueryOptions<TVariables, TItem, TExtractedData>): PaginatedQueryResult<TExtractedData> {
  const searchParams = useSearchParams();

  const prefix = typeof urlSync === "string" ? `${urlSync}-` : "";
  const pageKey = `${prefix}page`;
  const searchKey = `${prefix}search`;
  const perPageKey = `${prefix}per-page`;
  const sortKey = `${prefix}sort`;

  // Read initial values from URL once on mount — useState ignores subsequent changes
  const initialPage = urlSync ? parseInt(searchParams.get(pageKey) ?? "") || 1 : 1;
  const initialSearch = urlSync ? (searchParams.get(searchKey) ?? "") : "";
  const urlInitPerPage = urlSync ? parseInt(searchParams.get(perPageKey) ?? "") || null : null;

  // Initial filters from URL
  const initialFilterValues: Record<string, string> = {};
  if (urlSync && filterKeys.length > 0) {
    for (const key of filterKeys) {
      const val = searchParams.get(`${prefix}filter-${key}`);
      if (val) initialFilterValues[key] = val;
    }
  }

  // Initial sorting from URL: ?${prefix}sort=columnId:asc|desc
  const initialSorting: SortingState = [];
  if (urlSync) {
    const sortVal = searchParams.get(sortKey);
    if (sortVal) {
      const colonIdx = sortVal.lastIndexOf(":");
      const id = colonIdx > 0 ? sortVal.slice(0, colonIdx) : sortVal;
      const dir = colonIdx > 0 ? sortVal.slice(colonIdx + 1) : "asc";
      if (id) initialSorting.push({ id, desc: dir === "desc" });
    }
  }

  const [storedPerPage, setStoredPerPage] = useLocalStorage<number>(
    storageKey,
    sanitizePerPage(urlInitPerPage ?? initialPerPage ?? DEFAULT_PER_PAGE)
  );
  const perPage = sanitizePerPage(storedPerPage);

  const [page, setPage] = useState(initialPage);
  const [search, setSearch] = useState(initialSearch);
  const debouncedSearch = useDebounce(search, 300);
  const [filterValues, setFilterValuesState] =
    useState<Record<string, string | undefined>>(initialFilterValues);
  const [sorting, setSortingState] = useState<SortingState>(initialSorting);

  // Sync page, search, perPage, filters, and sort to the address bar after state commits.
  // Uses window.history.replaceState — NOT router.replace — to avoid triggering a
  // Next.js navigation, which would remount the component and reset React state.
  useEffect(() => {
    if (!urlSync) return;
    const params = new URLSearchParams(window.location.search);

    if (page === 1) params.delete(pageKey);
    else params.set(pageKey, String(page));

    if (!search) params.delete(searchKey);
    else params.set(searchKey, search);

    if (perPage === DEFAULT_PER_PAGE) params.delete(perPageKey);
    else params.set(perPageKey, String(perPage));

    for (const key of filterKeys) {
      const val = filterValues[key];
      if (val) params.set(`${prefix}filter-${key}`, val);
      else params.delete(`${prefix}filter-${key}`);
    }

    if (sorting.length > 0) {
      const { id, desc } = sorting[0];
      params.set(sortKey, `${id}:${desc ? "desc" : "asc"}`);
    } else {
      params.delete(sortKey);
    }

    const qs = params.toString();
    window.history.replaceState(null, "", qs ? `?${qs}` : window.location.pathname);
    // keys and urlSync are stable; exclude to avoid stale closure lint noise
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page, search, perPage, filterValues, sorting]);

  const queryOffset = (page - 1) * perPage;

  const filterVars = variablesFromFilters ? variablesFromFilters(filterValues) : {};
  const sortingVars = variablesFromSorting ? variablesFromSorting(sorting) : {};

  const mergedVariables = stripNullish({
    ...(variables as Record<string, unknown>),
    ...(filterVars as Record<string, unknown>),
    ...(sortingVars as Record<string, unknown>),
    first: perPage,
    offset: queryOffset,
    ...(debouncedSearch ? { search: debouncedSearch } : {}),
  }) as TVariables;

  const { data, loading, error, refetch } = useQuery<TData, TVariables>(query, {
    variables: mergedVariables,
    skip: shouldSkip,
    fetchPolicy,
    errorPolicy,
  });

  const ancestorData = (
    data as Record<string, { edges: TItem[]; totalCount: number } | null | undefined> | undefined
  )?.[ancestor];

  const edges = ancestorData?.edges ?? [];
  const totalCount = ancestorData?.totalCount ?? 0;
  const nodes = dataExtractor(edges);
  const totalPageCount = totalCount > 0 ? Math.ceil(totalCount / perPage) : 1;

  // Clamp page to valid range — but ONLY when not loading.
  // During a page change, Apollo briefly returns data=undefined (no cache hit), making
  // totalCount=0 and totalPageCount=1. Without the loading guard the clamp would fire
  // and reset the page back to 1 before the new data arrives.
  useEffect(() => {
    if (loading) return;
    const safe = sanitizePage(page, totalPageCount);
    if (safe !== page) setPage(safe);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [totalPageCount, loading]);

  const displayOffset = totalCount === 0 ? 0 : queryOffset + 1;
  const tailOffset = Math.min(queryOffset + perPage, totalCount);

  const goToPage = (p: number) => setPage(sanitizePage(p, totalPageCount));
  const nextPage = () => goToPage(page + 1);
  const prevPage = () => goToPage(page - 1);

  const handleSetPerPage = (n: number) => {
    setStoredPerPage(sanitizePerPage(n));
    setPage(1);
  };

  const handleSetSearch = (s: string) => {
    setSearch(s);
    setPage(1);
  };

  const setFilter = (id: string, value: string | undefined) => {
    setFilterValuesState((prev) => ({ ...prev, [id]: value }));
    setPage(1);
  };

  const setSorting = (newSorting: SortingState) => {
    setSortingState(newSorting);
  };

  const columnFiltersState: ColumnFiltersState = Object.entries(filterValues)
    .filter(([, v]) => v !== undefined && v !== "")
    .map(([id, value]) => ({ id, value }));

  const onFiltersChange = (next: ColumnFiltersState) => {
    for (const key of filterKeys) {
      const found = next.find((f) => f.id === key);
      setFilter(key, found?.value as string | undefined);
    }
  };

  return {
    nodes,
    totalCount,
    page,
    totalPageCount,
    loading,
    error,
    refetch: () => {
      void refetch();
    },
    goToPage,
    nextPage,
    prevPage,
    perPage,
    setPerPage: handleSetPerPage,
    search,
    setSearch: handleSetSearch,
    offset: displayOffset,
    tailOffset,
    filterValues,
    setFilter,
    onFiltersChange,
    columnFiltersState,
    sorting,
    setSorting,
  };
}
