// Manual types for the user domain.
// Once GraphQL Codegen is configured, replace these with imports from __generated__/graphql.ts

// --- Schema shapes ---

export type UserProfile = {
  id: string;
  username: string | null;
};

export type CurrentUser = {
  id: string;
  profile: UserProfile | null;
};

// --- Query types ---

export type MeQueryData = {
  me: CurrentUser | null;
};

export type MeQueryVariables = Record<string, never>;

// --- Mutation types (add as needed) ---
// export type UpdateProfileVariables = { input: { id: string; username: string } };
