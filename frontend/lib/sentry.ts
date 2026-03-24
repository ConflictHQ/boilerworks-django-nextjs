import * as Sentry from "@sentry/nextjs";

import type { CurrentUser } from "@/graphql/user/user.types";

const enabled = !!process.env.NEXT_PUBLIC_SENTRY_DSN;

/**
 * Identify the current user in Sentry.
 * Call this once after the user is resolved (e.g. in a layout or after login).
 * Pass `null` to clear the user (on logout).
 */
export function setSentryUser(user: CurrentUser | null) {
  if (!enabled) return;
  if (user) {
    Sentry.setUser({
      id: user.id,
      username: user.profile?.username ?? undefined,
    });
  } else {
    Sentry.setUser(null);
  }
}

/**
 * Capture an exception in Sentry with optional extra context.
 */
export function captureException(
  error: unknown,
  context?: Parameters<typeof Sentry.captureException>[1]
) {
  if (!enabled) return;
  Sentry.captureException(error, context);
}
