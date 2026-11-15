import type { StorybookConfig } from "@storybook/nextjs-vite";

/**
 * The app's own catalog: its layer on top of @calliopelabs/ui (ui-app/),
 * its components and its screens. Deployed as its own Astrolift app
 * (storybook/astrolift.toml) and composed into the Calliope AI UX front door.
 */
const config: StorybookConfig = {
  framework: "@storybook/nextjs-vite",
  stories: [
    "../ui-app/**/*.stories.@(ts|tsx)",
    "../components/**/*.stories.@(ts|tsx)",
    "../app/**/*.stories.@(ts|tsx)",
  ],
  addons: ["@storybook/addon-a11y"],
  staticDirs: ["../public"],
  core: { disableTelemetry: true },
  async viteFinal(viteConfig) {
    const { mergeConfig } = await import("vite");
    return mergeConfig(viteConfig, {
      // `staticDirs` copies public/; Vite's own publicDir copy of the same
      // folder races it into storybook-static.
      publicDir: false,
      build: { chunkSizeWarningLimit: 4096 },
    });
  },
};

export default config;
