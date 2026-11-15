"use client";

import { ErrorState } from "@calliopelabs/ui";
import { useEffect } from "react";
import { captureException } from "@/lib/sentry";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error(error);
    captureException(error);
  }, [error]);

  return (
    <div className="flex flex-1 flex-col items-center justify-center p-6">
      <ErrorState variant="page" error={error} digest={error.digest} onRetry={reset} homeHref="/" />
    </div>
  );
}
