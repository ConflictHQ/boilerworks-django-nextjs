"use client";

import * as React from "react";
import { type Table } from "@tanstack/react-table";
import { ListFilterIcon, XIcon } from "lucide-react";
import { useTranslations } from "next-intl";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { type FilterConfig } from "./types";

// ─── helpers ──────────────────────────────────────────────────────────────────

const EMPTY: Record<string, string> = {};

const emptyValue = (f: FilterConfig) => (f.type === "select" ? "all" : "");

const isActive = (f: FilterConfig, v: string) =>
  f.type === "select" ? v !== "all" && v !== "" : v !== "";

const toFilterValue = (f: FilterConfig, v: string) => (isActive(f, v) ? v : undefined);

// ─── filter chips ─────────────────────────────────────────────────────────────

const FilterChips = <TData,>({
  table,
  filters,
}: {
  table: Table<TData>;
  filters: FilterConfig[];
}) => {
  const columnFilters = table.getState().columnFilters;
  if (!columnFilters.length) return null;

  return (
    <div className="flex flex-wrap gap-1.5">
      {columnFilters.map((filter) => {
        const config = filters.find((f) => f.id === filter.id);
        const rawValue = filter.value as string;
        const label =
          config?.type === "select"
            ? (config.options?.find((o) => o.value === rawValue)?.label ?? rawValue)
            : rawValue;

        return (
          <Badge key={filter.id} variant="secondary" className="gap-1 pr-1 font-normal">
            <span className="capitalize">{config?.label ?? filter.id}:</span>
            <span className="font-medium">{label}</span>
            <button
              onClick={() => table.getColumn(filter.id)?.setFilterValue(undefined)}
              className="ml-0.5 rounded-sm opacity-60 hover:opacity-100"
            >
              <XIcon className="h-3 w-3" />
            </button>
          </Badge>
        );
      })}
    </div>
  );
};

// ─── filter panel ─────────────────────────────────────────────────────────────

const FilterPanel = <TData,>({
  table,
  filters,
}: {
  table: Table<TData>;
  filters: FilterConfig[];
}) => {
  const t = useTranslations("dataTable");
  const [open, setOpen] = React.useState(false);
  const [draft, setDraft] = React.useState<Record<string, string>>(EMPTY);

  const handleOpen = (next: boolean) => {
    if (next) {
      const current: Record<string, string> = {};
      filters.forEach((f) => {
        current[f.id] = (table.getColumn(f.id)?.getFilterValue() as string) ?? emptyValue(f);
      });
      setDraft(current);
    }
    setOpen(next);
  };

  const handleApply = () => {
    filters.forEach((f) => {
      table.getColumn(f.id)?.setFilterValue(toFilterValue(f, draft[f.id] ?? ""));
    });
    setOpen(false);
  };

  const handleClearAll = () => {
    const cleared: Record<string, string> = {};
    filters.forEach((f) => {
      cleared[f.id] = emptyValue(f);
    });
    setDraft(cleared);
  };

  const setField = (id: string, value: string) => setDraft((d) => ({ ...d, [id]: value }));

  const activeCount = table.getState().columnFilters.length;

  return (
    <Popover open={open} onOpenChange={handleOpen}>
      <PopoverTrigger asChild>
        <Button variant="outline" size="sm" className="h-8 gap-2">
          <ListFilterIcon className="h-3.5 w-3.5" />
          {t("filters")}
          {activeCount > 0 && <Badge className="h-4 min-w-4 px-1 text-[10px]">{activeCount}</Badge>}
        </Button>
      </PopoverTrigger>
      <PopoverContent align="start" className="w-64 p-0">
        <div className="flex items-center justify-between px-3 py-2.5">
          <p className="text-sm font-medium">{t("panel.title")}</p>
          <button
            onClick={handleClearAll}
            className="text-muted-foreground hover:text-foreground text-xs"
          >
            {t("panel.clearAll")}
          </button>
        </div>
        <Separator />

        <div className="flex flex-col gap-4 p-3">
          {filters.map((filter) => (
            <div key={filter.id} className="flex flex-col gap-1.5">
              <p className="text-muted-foreground text-xs font-medium tracking-wide uppercase">
                {filter.label}
              </p>

              {filter.type === "text" ? (
                <div className="relative">
                  <Input
                    className="h-8 pr-7"
                    placeholder={
                      filter.placeholder ?? t("panel.placeholder", { label: filter.label })
                    }
                    value={draft[filter.id] ?? ""}
                    onChange={(e) => setField(filter.id, e.target.value)}
                  />
                  {draft[filter.id] && (
                    <button
                      onClick={() => setField(filter.id, "")}
                      className="text-muted-foreground hover:text-foreground absolute top-1/2 right-2 -translate-y-1/2"
                    >
                      <XIcon className="h-3.5 w-3.5" />
                    </button>
                  )}
                </div>
              ) : (
                <Select
                  value={draft[filter.id] ?? "all"}
                  onValueChange={(v) => setField(filter.id, v)}
                >
                  <SelectTrigger className="h-8">
                    <SelectValue placeholder={t("panel.all")} />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">{t("panel.all")}</SelectItem>
                    {filter.options?.map((opt) => (
                      <SelectItem key={opt.value} value={opt.value}>
                        {opt.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}
            </div>
          ))}
        </div>

        <Separator />
        <div className="flex justify-end gap-2 p-2">
          <Button variant="ghost" size="sm" onClick={() => setOpen(false)}>
            {t("panel.cancel")}
          </Button>
          <Button size="sm" onClick={handleApply}>
            {t("panel.apply")}
          </Button>
        </div>
      </PopoverContent>
    </Popover>
  );
};

// ─── toolbar ──────────────────────────────────────────────────────────────────

type DataTableToolbarProps<TData> = {
  table: Table<TData>;
  filters?: FilterConfig[];
  searchPlaceholder?: string;
};

export const DataTableToolbar = <TData,>({
  table,
  filters = [],
  searchPlaceholder,
}: DataTableToolbarProps<TData>) => {
  const t = useTranslations("dataTable");
  const isFiltered = !!table.getState().globalFilter || table.getState().columnFilters.length > 0;

  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center gap-2">
        <Input
          placeholder={searchPlaceholder ?? t("search")}
          value={table.getState().globalFilter ?? ""}
          onChange={(e) => table.setGlobalFilter(e.target.value)}
          className="h-8 w-56"
        />
        {filters.length > 0 && <FilterPanel table={table} filters={filters} />}
        {isFiltered && (
          <Button
            variant="ghost"
            size="sm"
            className="text-muted-foreground h-8"
            onClick={() => {
              table.setGlobalFilter("");
              table.resetColumnFilters();
            }}
          >
            <XIcon className="h-3.5 w-3.5" />
            {t("clearAll")}
          </Button>
        )}
      </div>
      {filters.length > 0 && <FilterChips table={table} filters={filters} />}
    </div>
  );
};
