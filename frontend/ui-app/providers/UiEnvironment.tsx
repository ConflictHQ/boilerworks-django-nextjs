"use client";

import { type LinkProps, type MessageOverrides, UIProvider } from "@calliopelabs/ui";
import NextLink from "next/link";
import { useLocale, useTranslations } from "next-intl";
import { type ReactNode, useMemo } from "react";

/** next/link for every link a @calliopelabs/ui component draws. */
function Link({ href, ...props }: LinkProps) {
  return <NextLink href={href} {...props} />;
}

/**
 * The environment @calliopelabs/ui components read through `useUI()`:
 * client-side links and the app's own translations. Every string the library
 * renders comes from the `ui` namespace of messages/<locale>.json, so the
 * shell, tables, dialogs and the appearance picker follow the person's
 * language. Mount inside NextIntlClientProvider.
 */
export function UiEnvironment({ children }: { children: ReactNode }) {
  const t = useTranslations("ui");
  const locale = useLocale();

  const messages = useMemo<MessageOverrides>(() => {
    // A table's label mid-sentence: English lowercases it ("Could not load
    // employees"); other locales keep the caller's casing.
    const noun = (label: string) =>
      locale.startsWith("en") ? label.toLocaleLowerCase(locale) : label;
    return {
      shell: {
        skipToContent: t("shell.skipToContent"),
        navigation: t("shell.navigation"),
        close: t("shell.close"),
      },
      nav: {
        label: t("nav.label"),
        collapse: t("nav.collapse"),
        expand: t("nav.expand"),
        collapseTitle: t("nav.collapseTitle"),
        expandTitle: t("nav.expandTitle"),
      },
      breadcrumb: {
        label: t("breadcrumb.label"),
        switchFrom: (label) => t("breadcrumb.switchFrom", { label }),
      },
      table: {
        search: t("table.search"),
        clearSearch: t("table.clearSearch"),
        results: (count) => t("table.results", { count }),
        filteredResults: t("table.filteredResults"),
        loading: t("table.loading"),
        loadFailed: (label) => t("table.loadFailed", { label: noun(label) }),
        requestFailed: t("table.requestFailed"),
        retry: t("table.retry"),
        noMatches: t("table.noMatches"),
        noMatchesDescription: (label) => t("table.noMatchesDescription", { label: noun(label) }),
        selected: (count) => t("table.selected", { count }),
        clearSelection: t("table.clearSelection"),
        selectRow: (id) => t("table.selectRow", { id }),
        selectPage: (label) => t("table.selectPage", { label: noun(label) }),
        actions: t("table.actions"),
        rowActions: (label) => t("table.rowActions", { label }),
        rowsPerPage: t("table.rowsPerPage"),
        page: (page) => t("table.page", { page }),
        previousPage: t("table.previousPage"),
        nextPage: t("table.nextPage"),
        sortKey: (index) => t("table.sortKey", { index }),
      },
      states: {
        errorTitle: t("states.errorTitle"),
        unexpected: t("states.unexpected"),
        retry: t("states.retry"),
        errorId: (digest) => t("states.errorId", { digest }),
        loading: t("states.loading"),
        learnMore: t("states.learnMore"),
      },
      dialog: { close: t("dialog.close") },
      confirm: {
        confirm: t("confirm.confirm"),
        cancel: t("confirm.cancel"),
        working: t("confirm.working"),
        failed: t("confirm.failed"),
        reasonRequired: t("confirm.reasonRequired"),
      },
      user: {
        accountMenu: (name, initials) => t("user.accountMenu", { name, initials }),
        signOut: t("user.signOut"),
      },
      appearance: {
        locked: t("appearance.locked"),
        themes: t("appearance.themes"),
        accent: t("appearance.accent"),
        ground: t("appearance.ground"),
        density: t("appearance.density"),
        corners: t("appearance.corners"),
        reset: t("appearance.reset"),
        mode: (mode) => t(`appearance.modes.${mode}`),
        densityLabel: (density) => t(`appearance.densities.${density}`),
        densityHint: (density) => t(`appearance.densityHints.${density}`),
        cornersLabel: (corners) =>
          corners === 0
            ? t("appearance.cornerSquare")
            : corners === 10
              ? t("appearance.cornerRounded")
              : `${corners}px`,
        customAccent: t("appearance.customAccent"),
        customAccentPick: t("appearance.customAccentPick"),
        customAccentHelp: t("appearance.customAccentHelp"),
        customAccentInvalid: t("appearance.customAccentInvalid"),
        customAccentInUse: t("appearance.customAccentInUse"),
        customAccentOk: (ratio) => t("appearance.customAccentOk", { ratio }),
        customAccentFaint: (ratio, min, mode) =>
          t(
            mode === "dark"
              ? "appearance.customAccentFaintLighter"
              : "appearance.customAccentFaintDarker",
            { ratio, min }
          ),
      },
    };
  }, [t, locale]);

  return (
    <UIProvider link={Link} messages={messages}>
      {children}
    </UIProvider>
  );
}
