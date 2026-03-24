import { TypePolicies } from "@apollo/client";
import { InMemoryCache } from "@apollo/client-integration-nextjs";

// Default merge: true for all object types.
// Override specific types or fields below when needed
// (e.g. paginated list fields should NOT use merge: true).
const defaultTypePolicies = new Proxy({} as TypePolicies, {
  get: () => ({ merge: true }),
});

const cacheConfig = { typePolicies: defaultTypePolicies };

// SSR — fresh cache per request to prevent data leaking between users
export const makeCache = (): InMemoryCache => new InMemoryCache(cacheConfig);

// Client — singleton for the browser session lifetime
let _clientCache: InMemoryCache | null = null;
export const getClientCache = (): InMemoryCache =>
  (_clientCache ??= new InMemoryCache(cacheConfig));
