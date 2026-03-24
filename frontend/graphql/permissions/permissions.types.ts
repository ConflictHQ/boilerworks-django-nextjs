// Manual types for the permissions domain.
// Once GraphQL Codegen is configured, replace these with imports from __generated__/graphql.ts

export const enum PermissionSlug {
  SecuredPage = "secured-page",
}

export type PermissionComponent = { isActive: boolean };
export type PermissionQueryData = { component: PermissionComponent | null };
export type PermissionQueryVariables = { slug: string };
