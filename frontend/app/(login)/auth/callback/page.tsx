"use client";

import { useEffect, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";

function CallbackInner() {
  const router = useRouter();
  const searchParams = useSearchParams();

  useEffect(() => {
    const token = searchParams.get("token");
    if (!token) {
      router.replace("/auth/login");
      return;
    }

    // Store in localStorage for client-side Apollo
    localStorage.setItem("jwt", token);

    // Store in httpOnly cookie for server-side token reads
    fetch("/api/auth/store-token", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ token }),
    }).finally(() => {
      router.replace("/dashboard");
    });
  }, [router, searchParams]);

  return <div className="text-muted-foreground text-sm">Completing login…</div>;
}

export default function CallbackPage() {
  return (
    <Suspense fallback={<div className="text-muted-foreground text-sm">Loading…</div>}>
      <CallbackInner />
    </Suspense>
  );
}
