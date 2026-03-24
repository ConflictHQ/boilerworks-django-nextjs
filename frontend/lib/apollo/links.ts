import { ApolloLink, HttpLink } from "@apollo/client";
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

const errorLink = onError(({ graphQLErrors, networkError }) => {
  if (graphQLErrors) {
    for (const { extensions } of graphQLErrors) {
      if (extensions?.code === "UNAUTHENTICATED") {
        clearToken();
        window.location.href = "/auth/login";
        return;
      }
    }
  }
  if (networkError) {
    console.error("[Apollo] Network error:", networkError);
  }
});

export function buildClientLinks(httpLink: HttpLink): ApolloLink {
  return ApolloLink.from([errorLink, authLink.concat(httpLink)]);
}
