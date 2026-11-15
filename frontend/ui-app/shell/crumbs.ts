import { activeFor, areaSwitcher, type Crumb, type NavModel } from "@calliopelabs/ui";

/**
 * The breadcrumb for `pathname`, read from the navigation model so the
 * sidebar and the breadcrumb always agree: the area (switching between its
 * functions), the function, then the page itself when it sits below the
 * function (`/forms/abc` under Forms). Flat areas (Home) skip the area crumb.
 * `pageLabel` names that last page from its path segment.
 */
export function crumbsFor(
  nav: NavModel,
  pathname: string,
  pageLabel: (segment: string) => string
): Crumb[] {
  const active = activeFor(nav, pathname);
  if (!active) return [];
  const area = nav.find((a) => a.key === active.area);
  const fn = area?.groups.flatMap((g) => g.functions).find((f) => f.key === active.fn);
  if (!area || !fn) return [];

  const crumbs: Crumb[] = area.flat ? [] : [areaSwitcher(nav, area.key, fn.key)];
  const below = pathname !== fn.href && pathname.startsWith(`${fn.href}/`);
  crumbs.push(below ? { label: fn.label, href: fn.href } : { label: fn.label });
  if (below) {
    const segment = pathname.split("/").filter(Boolean).at(-1) ?? "";
    crumbs.push({ label: pageLabel(segment) });
  }
  return crumbs;
}
