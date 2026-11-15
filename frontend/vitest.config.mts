import { defineConfig } from "vitest/config";

/**
 * The web app's tests, in a browser-like DOM: the unit tests in __tests__/
 * and the catalog's tests in ui-app/test/. Stories render through the
 * catalog's own preview (.storybook/preview.tsx); the components they show
 * take the path and the person as props, so no Next.js router is needed.
 */
export default defineConfig({
  resolve: {
    alias: { "@": import.meta.dirname },
  },
  test: {
    environment: "jsdom",
    include: ["__tests__/**/*.test.{ts,tsx}", "ui-app/**/*.test.{ts,tsx}"],
    setupFiles: ["./ui-app/test/setup.ts"],
    // The a11y addon fails a story with violations only in a standalone
    // Vitest run, which it detects through this variable.
    env: { VITEST_STORYBOOK: "false" },
    server: { deps: { inline: ["@storybook/addon-a11y"] } },
  },
});
