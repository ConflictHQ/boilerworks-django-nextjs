"use client";

import { AppearanceProvider } from "@calliopelabs/ui";
import type { ReactNode } from "react";

import { product } from "@/ui-app/product";

/**
 * Ground, accent, density, corners and light or dark, from the library, with
 * the app's product. The product holds component references (its nav icons),
 * so it is imported here, in a client module, rather than passed as a prop
 * from the server layout.
 */
export function AppearanceRoot({ children }: { children: ReactNode }) {
  return <AppearanceProvider product={product}>{children}</AppearanceProvider>;
}
