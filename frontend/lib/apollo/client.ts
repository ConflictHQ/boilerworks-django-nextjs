import { ApolloLink, HttpLink } from "@apollo/client";
import { registerApolloClient, ApolloClient } from "@apollo/client-integration-nextjs";
import { cookies } from "next/headers";
import { fetchToken } from "@/lib/auth/fetch-token";
import { makeCache } from "./cache";

const API_URL = `${process.env.NEXT_PUBLIC_API_ROOT}/app/gql/config/`;

export const { getClient, query, PreloadQuery } = registerApolloClient(async () => {
  const cookieStore = await cookies();
  const cachedToken = cookieStore.get("backend_jwt")?.value;
  const token = cachedToken ?? (await fetchToken());

  const authLink = new ApolloLink((operation, forward) => {
    operation.setContext(({ headers = {} }: { headers?: Record<string, string> }) => ({
      headers: {
        ...headers,
        ...(token ? { Authorization: token } : {}),
        "x-platform": "web",
      },
    }));
    return forward(operation);
  });

  const httpLink = new HttpLink({ uri: API_URL });

  return new ApolloClient({
    cache: makeCache(),
    link: ApolloLink.from([authLink, httpLink]),
  });
});
