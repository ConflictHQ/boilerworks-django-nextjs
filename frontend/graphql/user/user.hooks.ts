"use client";

import { useQuery } from "@apollo/client/react";
import { GET_ME } from "./user.queries";
import type { MeQueryData, MeQueryVariables } from "./user.types";

export const useMe = () => {
  const { data, loading, error } = useQuery<MeQueryData, MeQueryVariables>(GET_ME, {
    fetchPolicy: "cache-first",
  });

  return {
    data,
    user: data?.me ?? null,
    loading,
    error,
  };
};
