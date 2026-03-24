"use client";

import { Badge } from "@/components/ui/badge";
import { useMe } from "@/graphql/user/user.hooks";

export default function AppUser() {
  const { user, loading } = useMe();

  if (loading) return null;
  if (!user) return null;

  return <Badge variant="secondary">{user.profile?.username ?? user.id}</Badge>;
}
