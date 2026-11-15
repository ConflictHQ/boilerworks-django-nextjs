import { readFileSync, readdirSync, statSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { describe, expect, it } from "vitest";

/**
 * Storybook first: every file under ui-app/ that defines a component has a
 * sibling story, with no allowlist. ui-app/providers/ (the app's context
 * wiring, which every story already runs through) and ui-app/test/ are exempt.
 */
const UI = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const EXEMPT = ["providers", "test"].map((dir) => `${path.sep}${dir}${path.sep}`);

function files(dir: string): string[] {
  return readdirSync(dir).flatMap((name) => {
    const full = path.join(dir, name);
    return statSync(full).isDirectory() ? files(full) : [full];
  });
}

describe("story coverage", () => {
  it("gives every component file under ui-app/ a sibling story", () => {
    const all = files(UI);
    const componentFiles = all.filter(
      (file) =>
        file.endsWith(".tsx") &&
        !/\.(stories|test)\.tsx$/.test(file) &&
        !EXEMPT.some((dir) => file.includes(dir)) &&
        /export (default )?function [A-Z]|export const [A-Z]\w* = |export \{/.test(
          readFileSync(file, "utf8")
        )
    );
    // A guard that the list is real, so the next assertion cannot pass empty.
    expect(componentFiles.length).toBeGreaterThan(3);
    const missing = componentFiles
      .filter((file) => !all.includes(file.replace(/\.tsx$/, ".stories.tsx")))
      .map((file) => path.relative(UI, file))
      .sort();
    expect(missing, `component files with no story (${missing.length})`).toEqual([]);
  });
});
