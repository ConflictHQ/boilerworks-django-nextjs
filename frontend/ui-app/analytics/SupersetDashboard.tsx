"use client";

import { EmptyState, ErrorState, LoadingState } from "@calliopelabs/ui";
import { embedDashboard } from "@superset-ui/embedded-sdk";
import { BarChart3Icon } from "lucide-react";
import { useTranslations } from "next-intl";
import * as React from "react";

import { cn } from "@/lib/utils";

export type SupersetDashboardProps = {
  /** Embedded dashboard UUID from Superset's "Embed dashboard" dialog. */
  embeddedId?: string | null;
  /** Superset origin the iframe loads from, e.g. https://superset.example.com. */
  supersetDomain?: string | null;
  /** Names the embed for assistive tech and the loading announcement. */
  title: string;
  /**
   * Returns a guest token issued by the app's backend. Called on mount and
   * again by the SDK before each token expires; never call Superset directly.
   */
  fetchGuestToken: () => Promise<string>;
  /** Height of the embedded dashboard in pixels. */
  height?: number;
  className?: string;
};

type Status = "loading" | "ready" | "error";

/**
 * A Superset dashboard embedded through @superset-ui/embedded-sdk, with the
 * app's loading, error and empty states. The browser only ever holds the
 * embedded id and short-lived guest tokens from `fetchGuestToken`.
 */
export function SupersetDashboard({
  embeddedId,
  supersetDomain,
  title,
  fetchGuestToken,
  height = 640,
  className,
}: SupersetDashboardProps) {
  const t = useTranslations("analytics");
  const mountRef = React.useRef<HTMLDivElement>(null);
  const [status, setStatus] = React.useState<Status>("loading");
  const [error, setError] = React.useState<string | null>(null);
  const [attempt, setAttempt] = React.useState(0);
  // The SDK calls fetchGuestToken for refreshes too; read the latest one.
  const fetchRef = React.useRef(fetchGuestToken);
  React.useEffect(() => {
    fetchRef.current = fetchGuestToken;
  }, [fetchGuestToken]);

  const configured = Boolean(embeddedId && supersetDomain);

  React.useEffect(() => {
    const mountPoint = mountRef.current;
    if (!configured || !mountPoint) return;
    let cancelled = false;
    let unmount: (() => void) | undefined;
    embedDashboard({
      id: embeddedId as string,
      supersetDomain: supersetDomain as string,
      mountPoint,
      fetchGuestToken: () => fetchRef.current(),
      iframeTitle: title,
      dashboardUiConfig: { hideTitle: true },
    }).then(
      (dashboard) => {
        if (cancelled) {
          dashboard.unmount();
          return;
        }
        unmount = dashboard.unmount;
        setStatus("ready");
      },
      (reason: unknown) => {
        if (cancelled) return;
        setError(reason instanceof Error ? reason.message : String(reason));
        setStatus("error");
      }
    );
    return () => {
      cancelled = true;
      unmount?.();
      mountPoint.replaceChildren();
    };
  }, [configured, embeddedId, supersetDomain, title, attempt]);

  if (!configured) {
    return (
      <EmptyState
        icon={<BarChart3Icon aria-hidden />}
        title={t("notConfiguredTitle")}
        description={t("notConfiguredDescription")}
        className={className}
      />
    );
  }

  return (
    <div className={cn("relative w-full", className)} style={{ minHeight: height }}>
      {status === "loading" && <LoadingState label={t("loading", { title })} />}
      {status === "error" && (
        <ErrorState
          title={t("loadFailed", { title })}
          error={error}
          onRetry={() => {
            setStatus("loading");
            setError(null);
            setAttempt((n) => n + 1);
          }}
          retryLabel={t("retry")}
        />
      )}
      {/* The SDK owns this node's children (the iframe); React never renders into it. */}
      <div
        ref={mountRef}
        data-slot="superset-dashboard"
        hidden={status !== "ready"}
        style={{ height }}
        className="w-full [&>iframe]:h-full [&>iframe]:w-full [&>iframe]:border-0"
      />
    </div>
  );
}
