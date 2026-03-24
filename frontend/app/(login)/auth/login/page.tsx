"use client";

import { useEffect } from "react";

export default function LoginPage() {
  useEffect(() => {
    const apiRoot = process.env.NEXT_PUBLIC_API_ROOT ?? "";
    const next = encodeURIComponent(`${window.location.origin}/auth/callback`);
    window.location.href = `${apiRoot}/app/auth1/login?next=${next}`;
  }, []);

  return (
    <div className="text-muted-foreground text-sm">Redirecting to login…</div>
  );
}
