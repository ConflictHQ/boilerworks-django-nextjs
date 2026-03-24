"use client";

import { useMe } from "@/graphql/user/user.hooks";

export default function Profile() {
  const { user, loading } = useMe();

  if (loading) return <p>Loading...</p>;
  if (!user) return null;

  return (
    <div>
      <p>{user.profile?.username}</p>
      <p>{user.email}</p>
    </div>
  );
}
