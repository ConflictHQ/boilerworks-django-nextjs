/// <reference types="vite/client" />
import * as a11yAnnotations from "@storybook/addon-a11y/preview";
import { composeStories, setProjectAnnotations } from "@storybook/react";
import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import * as previewAnnotations from "../../.storybook/preview";

/**
 * The a11y gate, as in @calliopelabs/ui: every story in the app renders
 * through the catalog's own decorators, runs its play function, and passes
 * the a11y addon's WCAG A and AA checks (the preview sets
 * `a11y.test: "error"`). A Storybook build only proves the stories compile;
 * this mounts each one. Colour contrast needs real CSS and layout, so in
 * jsdom it is left to the library's token contrast tests.
 */
setProjectAnnotations([a11yAnnotations, previewAnnotations]);

type PortableStory = {
  run: (context: {
    canvasElement: HTMLElement;
    testingLibraryRender: typeof render;
  }) => Promise<void>;
};

const modules = import.meta.glob<Record<string, unknown>>(
  [
    "../../ui-app/**/*.stories.tsx",
    "../../components/**/*.stories.tsx",
    "../../app/**/*.stories.tsx",
  ],
  { eager: true }
);

it("finds the stories", () => {
  // Guards against a glob that silently matches nothing.
  expect(Object.keys(modules).length).toBeGreaterThan(4);
});

describe.each(Object.entries(modules))("%s", (_file, module) => {
  const stories = Object.entries(
    composeStories(module as Parameters<typeof composeStories>[0])
  ) as [string, PortableStory][];
  it.each(stories)("%s renders", async (_name, story) => {
    const canvasElement = document.createElement("div");
    document.body.appendChild(canvasElement);
    await story.run({ canvasElement, testingLibraryRender: render });
    expect(canvasElement.childElementCount).toBeGreaterThan(0);
    canvasElement.remove();
  });
});
