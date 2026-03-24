import { Suspense } from "react";
import { Separator } from "@/components/ui/separator";
import { DataTable1 } from "@/components/DataTable1";
import { DataTableEmployees } from "@/components/DataTableEmployees";

export default function TablePage() {
  return (
    <div className="flex flex-1 flex-col gap-6 p-6">
      <div>
        <h1 className="text-xl font-semibold">Products</h1>
        <p className="text-muted-foreground mt-1 text-sm">
          Browse and manage your product inventory.
        </p>
      </div>
      <Separator />
      <DataTable1 />
      <Separator />
      <div>
        <h2 className="text-lg font-semibold">Server-side paginated (GraphQL)</h2>
        <p className="text-muted-foreground mt-1 text-sm">
          Live data from the GraphQL API with server-side pagination and search.
        </p>
      </div>
      <Suspense>
        <DataTableEmployees />
      </Suspense>
    </div>
  );
}
