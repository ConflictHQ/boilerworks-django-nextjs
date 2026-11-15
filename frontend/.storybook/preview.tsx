import "@fontsource/ibm-plex-sans/400.css";
import "@fontsource/ibm-plex-sans/500.css";
import "@fontsource/ibm-plex-sans/600.css";
import "@fontsource/ibm-plex-sans/700.css";
import "@fontsource/ibm-plex-mono/400.css";
import "@fontsource/ibm-plex-mono/500.css";
import "@fontsource-variable/dm-sans/index.css";
import "../app/globals.css";

import {
  AppearanceProvider,
  CORNERS,
  DENSITY_KEYS,
  productStyles,
  type Appearance,
} from "@calliopelabs/ui";
import type { Decorator, Preview } from "@storybook/nextjs-vite";
import { NextIntlClientProvider } from "next-intl";
import * as React from "react";

import messages from "../messages/en.json";
import { UiEnvironment } from "../ui-app/providers/UiEnvironment";
import { product } from "../ui-app/product";

/**
 * The toolbar's appearance, as the person's preference. Controlled, so the
 * toolbar never fights localStorage; the picker changes it here until the
 * toolbar moves again.
 */
function StoryAppearance({
  globals,
  children,
}: {
  globals: Record<string, string>;
  children: React.ReactNode;
}) {
  const [value, setValue] = React.useState<Partial<Appearance> | null>(() => ({
    ground: globals.ground as Appearance["ground"],
    accent: globals.accent === "product" ? product.defaults.accent : globals.accent,
    density: globals.density as Appearance["density"],
    corners: Number(globals.corners) as Appearance["corners"],
  }));
  return (
    <>
      <style data-calliope-ui="product">{productStyles(product)}</style>
      <AppearanceProvider product={product} value={value} onChange={setValue}>
        {children}
      </AppearanceProvider>
    </>
  );
}

/** The app's providers, as the root layout mounts them, in English. */
const withProviders: Decorator = (Story, context) => {
  const globals = context.globals as Record<string, string>;
  return (
    <NextIntlClientProvider locale="en" messages={messages} timeZone="UTC">
      <UiEnvironment>
        <StoryAppearance key={JSON.stringify(globals)} globals={globals}>
          <Story />
        </StoryAppearance>
      </UiEnvironment>
    </NextIntlClientProvider>
  );
};

const toolbar = (title: string, items: readonly (string | { value: string; title: string })[]) => ({
  description: title,
  toolbar: { title, items: [...items], dynamicTitle: true },
});

const preview: Preview = {
  decorators: [withProviders],
  // Each story starts from a person who has never folded the sidebar.
  beforeEach() {
    for (const key of Object.keys(window.localStorage)) {
      if (key.startsWith(`${product.id}.shell.`)) window.localStorage.removeItem(key);
    }
  },
  globalTypes: {
    ground: toolbar("Ground", product.grounds),
    accent: toolbar("Accent", [
      { value: "product", title: "Product accent" },
      ...product.accents.filter((a) => !a.brand).map((a) => ({ value: a.key, title: a.label })),
    ]),
    density: toolbar("Density", DENSITY_KEYS),
    corners: toolbar(
      "Corners",
      CORNERS.map((c) => ({ value: String(c), title: `${c}px` }))
    ),
  },
  initialGlobals: {
    ground: product.defaults.ground.dark,
    accent: "product",
    density: product.defaults.density,
    corners: String(product.defaults.corners),
  },
  parameters: {
    layout: "padded",
    backgrounds: { disable: true },
    controls: { expanded: true },
    nextjs: { appDirectory: true },
    a11y: {
      // Fail on violations (the story render test runs this too), against
      // the WCAG A and AA rules; best-practice rules are advice, not a gate.
      test: "error",
      options: {
        runOnly: {
          type: "tag",
          values: ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"],
        },
      },
    },
  },
};

export default preview;
