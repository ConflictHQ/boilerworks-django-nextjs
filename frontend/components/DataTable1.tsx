"use client";

import { type ColumnDef } from "@tanstack/react-table";
import { z } from "zod";
import { Badge } from "@/components/ui/badge";
import { DataTable, DataTableColumnHeader, type FilterConfig } from "@/components/data-table";

// ─── schema ───────────────────────────────────────────────────────────────────

export const schema = z.object({
  id: z.string(),
  item: z.string(),
  type: z.string(),
  stock: z.boolean(),
  sku: z.string(),
  price: z.number(),
  availability: z.array(z.enum(["In store", "Online"])),
});

type Product = z.infer<typeof schema>;

// ─── data ─────────────────────────────────────────────────────────────────────

const data: Product[] = schema.array().parse([
  {
    id: "prod-001",
    item: "Tablet Case",
    type: "Electronics",
    stock: true,
    sku: "TC-001",
    price: 83.24,
    availability: ["In store", "Online"],
  },
  {
    id: "prod-002",
    item: "Smart Watch",
    type: "Electronics",
    stock: true,
    sku: "SW-002",
    price: 246.27,
    availability: ["In store", "Online"],
  },
  {
    id: "prod-003",
    item: "Wool Sweater",
    type: "Accessories",
    stock: true,
    sku: "WS-003",
    price: 168.27,
    availability: ["In store"],
  },
  {
    id: "prod-004",
    item: "Wireless Earbuds",
    type: "Electronics",
    stock: true,
    sku: "WE-004",
    price: 107.75,
    availability: ["In store", "Online"],
  },
  {
    id: "prod-005",
    item: "Laptop Sleeve",
    type: "Electronics",
    stock: true,
    sku: "LS-005",
    price: 248.02,
    availability: ["In store", "Online"],
  },
  {
    id: "prod-006",
    item: "Running Shoes",
    type: "Footwear",
    stock: true,
    sku: "RS-006",
    price: 208.26,
    availability: ["In store"],
  },
  {
    id: "prod-007",
    item: "Winter Jacket",
    type: "Clothing",
    stock: false,
    sku: "WJ-007",
    price: 148.06,
    availability: ["In store"],
  },
  {
    id: "prod-008",
    item: "Phone Case",
    type: "Accessories",
    stock: true,
    sku: "PC-008",
    price: 298.08,
    availability: ["In store", "Online"],
  },
  {
    id: "prod-009",
    item: "Fitness Tracker",
    type: "Electronics",
    stock: true,
    sku: "FT-009",
    price: 222.09,
    availability: ["In store"],
  },
  {
    id: "prod-010",
    item: "Sunglasses",
    type: "Accessories",
    stock: false,
    sku: "SG-010",
    price: 60.17,
    availability: ["In store"],
  },
  {
    id: "prod-011",
    item: "Yoga Mat",
    type: "Sports",
    stock: true,
    sku: "YM-011",
    price: 45.99,
    availability: ["Online"],
  },
  {
    id: "prod-012",
    item: "Leather Wallet",
    type: "Accessories",
    stock: true,
    sku: "LW-012",
    price: 89.5,
    availability: ["In store", "Online"],
  },
  {
    id: "prod-013",
    item: "Bluetooth Speaker",
    type: "Electronics",
    stock: true,
    sku: "BS-013",
    price: 134.0,
    availability: ["Online"],
  },
  {
    id: "prod-014",
    item: "Baseball Cap",
    type: "Clothing",
    stock: true,
    sku: "BC-014",
    price: 29.99,
    availability: ["In store", "Online"],
  },
  {
    id: "prod-015",
    item: "Hiking Boots",
    type: "Footwear",
    stock: false,
    sku: "HB-015",
    price: 175.0,
    availability: ["In store"],
  },
  {
    id: "prod-016",
    item: "Water Bottle",
    type: "Sports",
    stock: true,
    sku: "WB-016",
    price: 24.95,
    availability: ["In store", "Online"],
  },
  {
    id: "prod-017",
    item: "Desk Lamp",
    type: "Electronics",
    stock: true,
    sku: "DL-017",
    price: 59.99,
    availability: ["Online"],
  },
  {
    id: "prod-018",
    item: "Canvas Tote",
    type: "Accessories",
    stock: true,
    sku: "CT-018",
    price: 18.0,
    availability: ["In store", "Online"],
  },
  {
    id: "prod-019",
    item: "Denim Jeans",
    type: "Clothing",
    stock: true,
    sku: "DJ-019",
    price: 94.0,
    availability: ["In store"],
  },
  {
    id: "prod-020",
    item: "Foam Roller",
    type: "Sports",
    stock: true,
    sku: "FR-020",
    price: 32.5,
    availability: ["Online"],
  },
]);

// ─── columns ──────────────────────────────────────────────────────────────────

const columns: ColumnDef<Product, unknown>[] = [
  {
    accessorKey: "sku",
    header: ({ column }) => <DataTableColumnHeader column={column} title="SKU" />,
    filterFn: (row, _id, value) => {
      if (!value) return true;
      return (row.getValue("sku") as string).toLowerCase().includes(value.toLowerCase());
    },
    enableSorting: true,
  },
  {
    accessorKey: "item",
    header: ({ column }) => <DataTableColumnHeader column={column} title="Item" />,
    cell: ({ row }) => <div className="font-medium">{row.getValue("item")}</div>,
    enableSorting: true,
  },
  {
    accessorKey: "type",
    header: ({ column }) => <DataTableColumnHeader column={column} title="Type" />,
    enableSorting: true,
  },
  {
    accessorKey: "stock",
    header: ({ column }) => <DataTableColumnHeader column={column} title="In Stock" />,
    cell: ({ row }) => (row.getValue("stock") ? "Yes" : "No"),
    filterFn: (row, _id, value) => {
      if (!value || value === "all") return true;
      return value === "true" ? row.getValue("stock") === true : row.getValue("stock") === false;
    },
    enableSorting: false,
  },
  {
    accessorKey: "price",
    header: ({ column }) => <DataTableColumnHeader column={column} title="Price" />,
    cell: ({ row }) => (
      <div className="font-medium">
        {new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(
          parseFloat(row.getValue("price"))
        )}
      </div>
    ),
    enableSorting: true,
  },
  {
    accessorKey: "availability",
    header: ({ column }) => <DataTableColumnHeader column={column} title="Available In" />,
    cell: ({ row }) => {
      const availability: ("In store" | "Online")[] = row.getValue("availability");
      return (
        <div className="flex gap-2">
          {availability.map((loc) => (
            <Badge key={loc} variant="secondary">
              {loc}
            </Badge>
          ))}
        </div>
      );
    },
    filterFn: (row, _id, value) => {
      if (!value) return true;
      const availability = row.getValue("availability") as string[];
      return availability.includes(value);
    },
    enableSorting: false,
  },
];

// ─── filter config ────────────────────────────────────────────────────────────

const TYPES = [...new Set(data.map((d) => d.type))].sort();

const filters: FilterConfig[] = [
  {
    id: "type",
    label: "Type",
    type: "select",
    options: TYPES.map((t) => ({ value: t, label: t })),
  },
  {
    id: "stock",
    label: "Stock",
    type: "select",
    options: [
      { value: "true", label: "In stock" },
      { value: "false", label: "Out of stock" },
    ],
  },
  {
    id: "availability",
    label: "Available in",
    type: "select",
    options: [
      { value: "In store", label: "In store" },
      { value: "Online", label: "Online" },
    ],
  },
  {
    id: "sku",
    label: "SKU",
    type: "text",
    placeholder: "e.g. TC-001",
  },
];

// ─── component ────────────────────────────────────────────────────────────────

export const DataTable1 = () => (
  <DataTable
    data={data}
    columns={columns}
    getRowId={(row) => row.id}
    pageSize={5}
    filters={filters}
    searchPlaceholder="Search items or SKU…"
  />
);
