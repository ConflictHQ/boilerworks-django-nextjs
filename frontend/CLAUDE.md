# frontend_app — Claude Context

## Stack

- Next.js 16 (App Router) + TypeScript
- Apollo Client 4 + `@apollo/client-integration-nextjs`
- Django session auth (via `auth1` backend) + backend JWT in `httpOnly` cookie
- Tailwind CSS 4 + [`@calliopelabs/ui`](https://www.npmjs.com/package/@calliopelabs/ui) (the Calliope AI design system); shadcn/ui for what the library lacks, in `ui-app/primitives/`
- Storybook 10 (`@storybook/nextjs-vite`) with an a11y gate in `npm test`
- Prettier + `prettier-plugin-tailwindcss` (formatting + Tailwind class sorting)

---

## Code formatting

Prettier is configured in `prettier.config.mjs`: double quotes, semicolons, 2-space indent,
ES5 trailing commas, `printWidth: 100`. `prettier-plugin-tailwindcss` sorts Tailwind class
names automatically. `eslint-config-prettier` (last in `eslint.config.mjs`) disables
conflicting ESLint rules.

**Scripts:**

- `npm run format` — rewrite all files in-place
- `npm run format:check` — CI check (exits 1 if any file would change)

Do not hand-tune whitespace, quote style, trailing commas, or line breaks — Prettier owns those.

---

## Page structure

Route groups:

- `app/(app)/` — authenticated pages; layout fetches `GET_ME` SSR and renders
  `AppChrome` + children
- `app/(login)/` — public; centered container, no sidebar
- Root `app/page.tsx` — redirects: session → `/dashboard`, no session → `/auth/login`

Provider nesting in root layout (outermost → innermost):
`AppearanceRoot` (library `AppearanceProvider`) → `Toaster` → `NextIntlClientProvider` → `UiEnvironment` (library `UIProvider`: `next/link` and the `ui` messages) → `ApolloWrapper` → `TooltipProvider` → `ConfirmProvider`. `AppearanceScript` in `<head>` sets the ground, accent and light or dark on `<html>` before first paint.

The signed-in layout renders `components/AppChrome.tsx` (the person, sign-out, the user drawers) around `ui-app/shell/AppFrame.tsx` (library `AppShell`, `Sidebar`, `BrandMark`, `UserMenu`, `Breadcrumbs`).

**Breadcrumbs** come from the navigation model in `ui-app/product.ts`: the area (switching
between its rows), the row, then the page when it sits below its row. That last page is
named from `routeLabels` (`lib/routes.ts`), falling back to the capitalised segment with
hyphens replaced by spaces.

**Adding a new page:**

1. Create `app/(app)/<route>/page.tsx` (Server Component by default)
2. Add a row to `NAV` in `ui-app/product.ts`, and its label to the `nav` namespace of every `messages/<locale>.json`
3. For a page below a row, add a route label in `lib/routes.ts`

**Page layout boilerplate:**

```tsx
import { PageHeader } from "@calliopelabs/ui";

export default function MyPage() {
  return (
    <div className="flex flex-1 flex-col gap-6 p-6">
      <PageHeader
        title="Title"
        description="Description."
        primaryAction={<Button size="sm">New</Button>}
      />
      <Separator />
      {/* content */}
    </div>
  );
}
```

**Components:** import from `@calliopelabs/ui` first (Button, Input, Checkbox, DropdownMenu,
Popover, Skeleton, AlertDialog, Drawer, Dialog, Tabs, PageHeader, DataTable, EmptyState,
ErrorState, LoadingState, StatusBadge). What the library lacks lives in `ui-app/primitives/`
(`npx shadcn add` writes there); every component in `ui-app/` has a sibling `.stories.tsx`.

---

## Forms

Stack: `react-hook-form` + `zod` + `@hookform/resolvers/zod`. Forms are always Client Components.

**Pattern:**

1. Define schema in a co-located `schema.ts`; export the inferred type
2. Build form component with `useForm<Values>({ resolver: zodResolver(schema), defaultValues })`
3. Use `register()` for `<Input>` / `<Textarea>`; use `<Controller>` for `<Select>` and other
   controlled components
4. In `onSubmit`: call mutation, `reset()` on success, `toast.error(...)` on failure
5. Disable submit button with `isSubmitting`

**UI components:** `Field`, `FieldLabel`, `FieldDescription`, `FieldError`, `FieldGroup`
(from `@/ui-app/primitives/field`) wrap each form control. Layout: grid with
`grid-cols-1 md:grid-cols-3`; section header in column 1, fields in `col-span-2`.

```typescript
// schema.ts
export const mySchema = z.object({
  name: z.string().min(1),
  role: z.enum(["admin", "member"]),
});
export type MyFormValues = z.infer<typeof mySchema>;

// component
const {
  register,
  control,
  handleSubmit,
  formState: { errors, isSubmitting },
  reset,
} = useForm<MyFormValues>({
  resolver: zodResolver(mySchema),
  defaultValues: { name: "", role: "member" },
});
```

---

## Toasts

Library: `sonner`. The `<Toaster>` is in root layout; theme is synced automatically.

```typescript
import { toast } from "sonner";

toast.success("Saved", { description: "Your changes have been applied." });
toast.error("Failed", { description: "Please try again." });
```

Always provide a title string and an optional `description`. No setup needed in individual components.

---

## Navigation

The navigation model is `NAV` in `ui-app/product.ts`: areas, groups and rows (`NavFunction`:
`key`, `label`, `href`, `icon`, optional `requires` and `also`). The sidebar, the breadcrumb
and the active row all read it. Labels are translated through `localizeNav` from the `nav`
namespace, keyed by each area's and row's `key`.

The user menu (`components/AppChrome.tsx`) shows the person from two sources: the SSR
`ssrUser` prop and the `useMe()` GraphQL hook. Sign-out calls `clearToken()` then redirects
to the backend's `/app/auth1/logout`.

---

## Data table

Lists use the library `DataTable`. It reads a `TableController` (rows, state, paging, search,
sort); the app supplies one of two, in `ui-app/table/`.

### Rows already in hand

```typescript
"use client";
import { DataTable, type Column } from "@calliopelabs/ui";
import { useLocalTable } from "@/ui-app/table/use-local-table";

const columns: Column<MyRow>[] = [
  { id: "name", header: "Name", sortKey: "name", cell: (r) => r.name },
];

const table = useLocalTable(rows, {
  matches: (r, q) => r.name.toLowerCase().includes(q),
  comparators: { name: (a, b) => a.name.localeCompare(b.name) },
  pageSize: 10,
});

<DataTable label="Things" controller={table} columns={columns} getRowId={(r) => r.id}
           empty={{ title: "No things yet" }} />
```

---

## Server-side paginated table

For GraphQL lists, `usePaginatedQuery` pages and searches on the server and
`paginatedController` (`ui-app/table/paginated-controller.ts`) hands its result to the
library `DataTable`. Filters go in the table's `toolbar` and call `setFilter`. Sorting stays
off in the controller until the query takes a sort argument (`variablesFromSorting`).

### usePaginatedQuery

Generic hook in `hooks/use-paginated-query.ts`. Manages page, search, perPage, filters, and sort — all optionally synced to URL params.

```typescript
const result = usePaginatedQuery<TVariables, TData, TItem, TExtractedData>({
  query, // DocumentNode
  variables, // static partial variables (merged with dynamic ones)
  ancestor, // key into data — e.g. "employees" → data.employees.edges / totalCount
  dataExtractor, // (edges: TItem[]) => TExtractedData[]
  storageKey, // localStorage key for persisted perPage preference
  fetchPolicy, // required — e.g. "cache-and-network"
  urlSync, // false | true | "prefix" — syncs page/search/perPage/filters/sort to URL
  filterKeys, // string[] — filter IDs to track, e.g. ["status"]
  variablesFromFilters, // (filters: Record<string, string | undefined>) => Partial<TVariables>
  variablesFromSorting, // (sorting: SortingState) => Partial<TVariables>
});
```

**Returns:**

| Field                                             | Description                                                                            |
| ------------------------------------------------- | -------------------------------------------------------------------------------------- |
| `nodes`                                           | Extracted data array                                                                   |
| `totalCount`, `page`, `totalPageCount`, `perPage` | Pagination state                                                                       |
| `loading`, `error`                                | Query state                                                                            |
| `nextPage`, `prevPage`, `goToPage`, `setPerPage`  | Pagination actions                                                                     |
| `search`, `setSearch`                             | Search state (debounced 300 ms before hitting the query)                               |
| `offset`, `tailOffset`                            | For display: "1–10 of 42"                                                              |
| `filterValues`                                    | `Record<string, string \| undefined>` — current filter state                           |
| `setFilter(id, value)`                            | Set or clear one filter; resets page to 1                                              |
| `onFiltersChange`                                 | Handler for a TanStack table's `onFiltersChange`; syncs all `filterKeys` automatically |
| `columnFiltersState`                              | `ColumnFiltersState` derived from `filterValues`                                       |
| `sorting`                                         | `SortingState` (once the query takes a sort argument)                                  |
| `setSorting`                                      | Sets the sort                                                                          |

**URL param format** (with `urlSync: "employee"` prefix):

| Param    | Example                          |
| -------- | -------------------------------- |
| Page     | `?employee-page=2`               |
| Search   | `?employee-search=alice`         |
| Per page | `?employee-per-page=20`          |
| Filter   | `?employee-filter-status=active` |
| Sort     | `?employee-sort=name:desc`       |

### Domain hook pattern

Co-locate columns and the hook in `graphql/<domain>/<domain>.hooks.tsx` (`.tsx` for JSX in column definitions):

```typescript
// graphql/employees/employees.hooks.tsx
export const employeeColumns: Column<Employee>[] = [ ... ];

export const useEmployees = (perPage?: number) => {
  const result = usePaginatedQuery<...>({
    query: getEmployees,
    variables: {},
    ancestor: "employees",
    dataExtractor: (edges) => edges.map((e) => e.node),
    storageKey: "employees-per-page",
    fetchPolicy: "cache-and-network",
    urlSync: "employee",
    filterKeys: ["status"],
    variablesFromFilters: (filters) => ({
      showDeactivated: filters.status === "active" ? false
                     : filters.status === "deactivated" ? true
                     : undefined,
    }),
  });
  return { ...result };
};
```

### DataTable wiring

```tsx
// components/DataTableEmployees.tsx
"use client";
import { DataTable } from "@calliopelabs/ui";
import { employeeColumns, useEmployees } from "@/graphql/employees/employees.hooks";
import { paginatedController } from "@/ui-app/table/paginated-controller";

export function DataTableEmployees() {
  const employees = useEmployees();
  return (
    <DataTable
      label="Employees"
      controller={paginatedController(employees)}
      columns={employeeColumns}
      getRowId={(row) => row.id}
      searchPlaceholder="Search employees…"
      empty={{ title: "No employees yet" }}
      toolbar={/* a status Select that calls employees.setFilter("status", …) */ null}
    />
  );
}
```

Wrap the consumer in `<Suspense>` when `urlSync` is enabled (required by `useSearchParams`):

```tsx
<Suspense>
  <DataTableEmployees />
</Suspense>
```

---

## Storybook

```bash
npm run storybook        # the catalog on port 6006
npm run build-storybook  # storybook-static/, served by storybook/Dockerfile
npm test                 # unit tests, every story rendered with WCAG A and AA checks, and story coverage for ui-app/
```

Stories live beside their component (`*.stories.tsx`) under `ui-app/`, `components/` or `app/`.
The preview (`.storybook/preview.tsx`) mounts the same providers as the root layout, in
English, with toolbar controls for the ground, accent, density and corners. Keep components
that a story shows pure: take the path, the person and data as props, and fetch in the route
or a connected wrapper.

---

## Auth flow

The backend `auth1` app authenticates the user (it handles the OIDC flow server-side).
The frontend never talks to the identity provider directly and has no auth SDK dependency.

**Login (browser):**

1. `/auth/login` redirects to `NEXT_PUBLIC_API_ROOT/app/auth1/login?next=<origin>/auth/callback`
2. The backend completes the OIDC flow and redirects back to `/auth/callback?token=<backend_jwt>`
3. The callback page stores the token in `localStorage` key `"jwt"` (for client-side Apollo)
   and POSTs it to `/api/auth/store-token`, which sets the `httpOnly` cookie `backend_jwt`
   (for server-side reads)

**Token on the server:**

- `lib/auth/fetch-token.ts` — `fetchToken()` reads the `backend_jwt` cookie (server-only)

**Token on the client:**

- `lib/auth/token-store.ts` reads from `localStorage` key `"jwt"`
- If not found, calls `POST /api/session/getToken` (route handler) which runs `fetchToken()` server-side
- `clearToken()` from `token-store.ts` must be called on logout — do NOT call `localStorage.removeItem` directly

**Key files:**

```
lib/auth/
  fetch-token.ts    — fetchToken(): backend_jwt cookie read (server-only)
  token-store.ts    — getClientToken() + clearToken() (browser-only)
```

---

## Apollo setup

Two clients — one for server (RSC), one for client components.

**Server client** (`lib/apollo/client.ts`):

- Uses `registerApolloClient` from `@apollo/client-integration-nextjs`
- Reads `backend_jwt` cookie, falls back to `fetchToken()`
- Exports `getClient`, `query`, `PreloadQuery`

**Client provider** (`lib/apollo/provider.tsx`):

- `"use client"` — wraps app in `ApolloNextAppProvider`
- Token injected per-request via `authLink` → `getClientToken()`
- Keyed on `user?.sub` — rebuilds Apollo client when user identity changes
- Includes `errorLink`: redirects to `/auth/login` on `UNAUTHENTICATED`

**Cache** (`lib/apollo/cache.ts`):

- `InMemoryCache` imported from `@apollo/client-integration-nextjs` (required for SSR)
- `typePolicies` defined explicitly — no Proxy catch-all
- Add `merge: true` per type as needed

**Public API** — always import Apollo from the barrel:

```typescript
import { getClient, PreloadQuery, ApolloWrapper } from "@/lib/apollo";
```

---

## GraphQL operations — file structure

All operations live in `graphql/<domain>/`:

```
graphql/
  user/
    user.fragments.ts   — gql fragments (add when schema type names are confirmed)
    user.queries.ts     — DocumentNode exports (GET_ME, etc.)
    user.mutations.ts   — mutation DocumentNode exports
    user.hooks.ts       — arrow-function hooks wrapping useQuery/useMutation
    user.types.ts       — manual TS types (replace with codegen later)
```

When adding a new domain (e.g. `orders`), create `graphql/orders/` with the same 5 files.

---

## Adding a new query

**1. Define types** in `user.types.ts`:

```typescript
export type MyQueryData = { thing: { id: string; name: string } | null };
export type MyQueryVariables = { id: string };
```

**2. Write the query** in `user.queries.ts`:

```typescript
export const GET_THING = gql`
  query GetThing($id: ID!) {
    thing(id: $id) {
      id
      name
    }
  }
`;
```

**3. Add a hook** in `user.hooks.ts`:

```typescript
export const useThing = (id: string) => {
  const { data, loading, error } = useQuery<MyQueryData, MyQueryVariables>(GET_THING, {
    variables: { id },
    fetchPolicy: "cache-first",
  });
  return { thing: data?.thing ?? null, loading, error };
};
```

**4. Use in a client component:**

```typescript
"use client";
import { useThing } from "@/graphql/user/user.hooks";
```

**5. Use in a server component (RSC):**

```typescript
import { getClient } from "@/lib/apollo";
import { GET_THING } from "@/graphql/user/user.queries";

const client = await getClient();
const { data } = await client.query({ query: GET_THING, variables: { id } });
```

---

## Adding a mutation

**1. Write the mutation** in `user.mutations.ts`:

```typescript
export const UPDATE_THING = gql`
  mutation UpdateThing($input: UpdateThingInput!) {
    updateThing(input: $input) {
      id
      name
    }
  }
`;
```

**2. Add a hook** in `user.hooks.ts`:

```typescript
export const useUpdateThing = () =>
  useMutation<UpdateThingData, UpdateThingVariables>(UPDATE_THING, {
    refetchQueries: [GET_THING],
  });
```

---

## Fragments

Fragments live in `user.fragments.ts`. Before using `fragment X on TypeName`, confirm the exact
type name from the backend schema — wrong type names return a 400 with "Unknown type" error.

```typescript
export const THING_FIELDS = gql`
  fragment ThingFields on ActualBackendTypeName {
    id
    name
  }
`;
```

Interpolate at the bottom of every query/mutation that uses it:

```typescript
export const GET_THING = gql`
  query GetThing($id: ID!) {
    thing(id: $id) {
      ...ThingFields
    }
  }
  ${THING_FIELDS}
`;
```

---

## RSC vs Client component rules

|               | Server Component               | Client Component                       |
| ------------- | ------------------------------ | -------------------------------------- |
| Data fetching | `await getClient().query(...)` | `useQuery` hook via `user.hooks.ts`    |
| Mutations     | not applicable                 | `useMutation` hook via `user.hooks.ts` |
| Auth state    | `fetchToken()` (cookie read)   | `useMe()` from `user.hooks.ts`         |

- Never use `useQuery` / `useMutation` in a Server Component
- Never use `getClient()` in a Client Component — use hooks instead
- Always import hooks from `@/graphql/<domain>/<domain>.hooks`, not `useQuery` directly

---

## Conventions

- Code style is enforced by Prettier — do not hand-tune formatting it controls
- Hooks use **arrow functions**: `export const useMe = () => { ... }`
- Query/mutation constants: `SCREAMING_SNAKE_CASE` (`GET_ME`, `UPDATE_PROFILE`)
- Paginated list query constants: `camelCase` (`getEmployees`, `getProducts`) — used with `usePaginatedQuery`
- Fragment names: `PascalCase` + `Fields` suffix (`ThingFields`)
- All `useQuery` calls must have explicit type params: `useQuery<Data, Variables>(...)`
- `fetchPolicy` must be set explicitly in every hook — no implicit defaults
- Component files in `components/`: **PascalCase** (`AppChrome.tsx`, `DataTableEmployees.tsx`). Files that contain JSX columns/filters co-located with their domain hook use `.tsx` extension (`employees.hooks.tsx`)

---

## Permission guards

The permission system checks whether a backend `component(slug)` is active before rendering a page or component. Two complementary patterns are available.

**Key files:**

```
graphql/permissions/
  permissions.types.ts   — PermissionSlug enum + GQL types (client-safe, source of truth)
  permissions.queries.ts — GET_PERMISSION query
  permissions.hooks.ts   — usePermission(slug) hook (client)
lib/permissions.ts       — checkPermission / requirePermission (server-only); re-exports PermissionSlug
components/PermissionGuard.tsx — PermissionGuard + withPermissionAuthenticationRequired (client)
```

### Adding a permission slug

All slugs live in the `const enum` in `graphql/permissions/permissions.types.ts` — the only file to touch:

```ts
export const enum PermissionSlug {
  SecuredPage = "secured-page",
  MyFeature = "my-feature", // add here
}
```

### Server guard (RSC pages)

Call `requirePermission` at the top of a Server Component page. If the slug is inactive or the backend is unreachable, Next.js serves the 404 page — no HTML is streamed to the client.

```tsx
import { requirePermission, PermissionSlug } from "@/lib/permissions";

export default async function MyPage() {
  await requirePermission(PermissionSlug.MyFeature);
  return <div>...</div>;
}
```

Use `checkPermission` when you need a boolean instead of an immediate 404:

```tsx
const allowed = await checkPermission(PermissionSlug.MyFeature);
```

`checkPermission` swallows network errors and returns `false` — safe to call when the backend may be down.

### Client guard

Import `PermissionSlug` from the types file (not `lib/permissions`) to avoid pulling server-only code into the client bundle.

**`PermissionGuard`** — wrap JSX directly:

```tsx
import { PermissionGuard } from "@/components/PermissionGuard";
import { PermissionSlug } from "@/graphql/permissions/permissions.types";

<PermissionGuard permission={PermissionSlug.MyFeature}>
  <MyContent />
</PermissionGuard>;
```

**`withPermissionAuthenticationRequired`** — HOC, mirrors the Pages Router API:

```tsx
import { withPermissionAuthenticationRequired } from "@/components/PermissionGuard";
import { PermissionSlug } from "@/graphql/permissions/permissions.types";

function MyComponent() { ... }
export const GuardedComponent = withPermissionAuthenticationRequired(MyComponent, PermissionSlug.MyFeature);
```

Both client patterns show a spinner while loading, call `notFound()` if `component.isActive === false`, and redirect to `/auth/logout` if `me` is null.

### Example page

`app/(app)/secured/` demonstrates both patterns with `PermissionSlug.SecuredPage`:

- `page.tsx` — RSC using `requirePermission`
- `secured-client-section.tsx` — client component using `withPermissionAuthenticationRequired`

---

## Codegen (not yet configured)

When codegen is added:

- Install `@graphql-codegen/cli` + `@graphql-codegen/client-preset`
- Output goes to `__generated__/graphql.ts`
- Replace manual types in `*.types.ts` with generated imports
- `TypedDocumentNode` from codegen will make explicit `useQuery<Data, Vars>` type params optional

---

## Utility hooks

All utility hooks live in `hooks/`. Import directly:

```typescript
import { useDebounce } from "@/hooks/use-debounce";
import { useLocalStorage } from "@/hooks/use-local-storage";
import { useCopyToClipboard } from "@/hooks/use-copy-to-clipboard";
import { useConfirm } from "@/hooks/use-confirm";
```

### useDebounce

```typescript
const debouncedSearch = useDebounce(searchValue, 300);
```

Delays updating `debouncedSearch` until `searchValue` has not changed for `delay` ms (default 300 ms).
Pair with a `useEffect` that fires the query on `debouncedSearch`.

### useLocalStorage

```typescript
const [view, setView] = useLocalStorage<string>("forms.view", "grid");
```

SSR-safe typed wrapper around `localStorage`. Initialises from stored JSON; falls back to `initialValue` on parse error.

### useCopyToClipboard

```typescript
const [copied, copy] = useCopyToClipboard();
// ...
<Button onClick={() => copy(text)}>{copied ? "Copied!" : "Copy"}</Button>
```

Uses `navigator.clipboard`. `copied` resets to `false` automatically after 2 s (configurable: `useCopyToClipboard(1000)`).

### useConfirm

Requires `<ConfirmProvider>` in the tree (already added to root layout).

```typescript
const confirm = useConfirm();
// ...
const ok = await confirm({
  title: "Delete item?",
  description: "This cannot be undone.",
  confirmLabel: "Delete",
  cancelLabel: "Cancel",
});
if (ok) deleteItem();
```

Returns a `Promise<boolean>`. Renders a single `AlertDialog` at the provider level — no local dialog state needed.
See `/hooks` page for a live example.
