"use client";

import { HttpLink } from "@apollo/client";
import { ApolloNextAppProvider, ApolloClient } from "@apollo/client-integration-nextjs";
import { buildClientLinks } from "./links";
import { getClientCache } from "./cache";

const API_URL = `${process.env.NEXT_PUBLIC_API_ROOT}/app/gql/config/`;

function makeClient(): ApolloClient {
  const httpLink = new HttpLink({ uri: API_URL });
  return new ApolloClient({
    link: buildClientLinks(httpLink),
    cache: getClientCache(),
  });
}

export function ApolloWrapper({ children }: { children: React.ReactNode }) {
  return (
    <ApolloNextAppProvider makeClient={makeClient}>
      {children}
    </ApolloNextAppProvider>
  );
}
