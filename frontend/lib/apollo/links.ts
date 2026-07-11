import { ApolloLink, HttpLink } from "@apollo/client";
import { CombinedGraphQLErrors } from "@apollo/client/errors";
import { setContext } from "@apollo/client/link/context";
import { onError } from "@apollo/client/link/error";
import { getClientToken, clearToken } from "@/lib/auth/token-store";

const authLink = setContext(async (_, { headers }) => {
  const token = await getClientToken();
  return {
    headers: {
      ...headers,
      ...(token ? { Authorization: token } : {}),
      "x-platform": "web",
    },
  };
});

const errorLink = onError(({ error }) => {
  if (CombinedGraphQLErrors.is(error)) {
    for (const { extensions } of error.errors) {
      if (extensions?.code === "UNAUTHENTICATED") {
        clearToken();
        window.location.href = "/auth/login";
        return;
      }
    }
  } else if (error) {
    console.error("[Apollo] Network error:", error);
  }
});

export function buildClientLinks(httpLink: HttpLink): ApolloLink {
  return ApolloLink.from([errorLink, authLink.concat(httpLink)]);
}
