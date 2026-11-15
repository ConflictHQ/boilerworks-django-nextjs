"use client";

import { DataTable, StatusBadge, type Column } from "@calliopelabs/ui";
import { z } from "zod";
import { Badge } from "@/ui-app/primitives/badge";
import { useLocalTable } from "@/ui-app/table/use-local-table";

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

const price = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" });

const columns: Column<Product>[] = [
  {
    id: "sku",
    header: "SKU",
    sortKey: "sku",
    cell: (p) => <span className="font-mono">{p.sku}</span>,
  },
  { id: "item", header: "Item", sortKey: "item", cell: (p) => p.item },
  { id: "type", header: "Type", sortKey: "type", cell: (p) => p.type },
  {
    id: "stock",
    header: "Stock",
    cell: (p) => (
      <StatusBadge tone={p.stock ? "ok" : "warn"}>
        {p.stock ? "In stock" : "Out of stock"}
      </StatusBadge>
    ),
  },
  {
    id: "price",
    header: "Price",
    sortKey: "price",
    align: "right",
    cell: (p) => <span className="font-medium">{price.format(p.price)}</span>,
  },
  {
    id: "availability",
    header: "Availability",
    cell: (p) => (
      <div className="flex gap-2">
        {p.availability.map((loc) => (
          <Badge key={loc} variant="secondary">
            {loc}
          </Badge>
        ))}
      </div>
    ),
  },
];

const comparators: Record<string, (a: Product, b: Product) => number> = {
  sku: (a, b) => a.sku.localeCompare(b.sku),
  item: (a, b) => a.item.localeCompare(b.item),
  type: (a, b) => a.type.localeCompare(b.type),
  price: (a, b) => a.price - b.price,
};

const matches = (p: Product, query: string) =>
  [p.item, p.sku, p.type].some((v) => v.toLowerCase().includes(query));

// ─── component ────────────────────────────────────────────────────────────────

/** A client-side table: the rows are all here, so search, sort and paging run locally. */
export const DataTable1 = () => {
  const table = useLocalTable(data, { matches, comparators, pageSize: 5, pageSizes: [5, 10, 20] });
  return (
    <DataTable
      label="Products"
      controller={table}
      columns={columns}
      getRowId={(p) => p.id}
      searchPlaceholder="Search items, SKU or type…"
      empty={{ title: "No products yet" }}
    />
  );
};
