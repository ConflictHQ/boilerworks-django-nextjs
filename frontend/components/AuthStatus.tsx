"use client";

import { Badge } from "@/components/ui/badge";
import LoginButton from "@/components/LoginButton";
import LogoutButton from "@/components/LogoutButton";
import { useMe } from "@/graphql/user/user.hooks";

export default function AuthStatus() {
  const { user, loading } = useMe();

  if (loading) {
    return <Badge variant="secondary">Loading...</Badge>;
  }

  return (
    <div className="flex items-center gap-3">
      {user ? (
        <>
          <Badge variant="default">{user.profile?.username ?? user.email}</Badge>
          <LogoutButton />
        </>
      ) : (
        <>
          <Badge variant="outline">Not signed in</Badge>
          <LoginButton />
        </>
      )}
    </div>
  );
}
