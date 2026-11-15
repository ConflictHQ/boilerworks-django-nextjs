import "@testing-library/jest-dom/vitest";

import { cleanup } from "@testing-library/react";
import { afterEach } from "vitest";

// Vitest runs without globals, so Testing Library's automatic cleanup never
// registers; without this, one test's DOM leaks into the next.
afterEach(() => {
  cleanup();
  window.localStorage.clear();
  for (const attribute of ["product", "ground", "mode", "accent", "density"]) {
    delete document.documentElement.dataset[attribute];
  }
  document.documentElement.removeAttribute("style");
});

// jsdom implements none of the browser APIs the Radix popper and focus code
// call on mount. Stub them once, globally, so tests exercise the real
// components instead of mocks of them.
globalThis.ResizeObserver ??= class {
  observe() {}
  unobserve() {}
  disconnect() {}
};
Element.prototype.scrollIntoView ??= function scrollIntoView() {};
Element.prototype.hasPointerCapture ??= function hasPointerCapture() {
  return false;
};
Element.prototype.setPointerCapture ??= function setPointerCapture() {};
Element.prototype.releasePointerCapture ??= function releasePointerCapture() {};
// axe-core probes a canvas for icon fonts; jsdom has none and says so on every call.
HTMLCanvasElement.prototype.getContext = (() =>
  null) as typeof HTMLCanvasElement.prototype.getContext;

// jsdom cannot navigate, and says so for every link a test follows. Stop the
// default action after the app's own handlers have run.
window.addEventListener("click", (event) => {
  if ((event.target as Element | null)?.closest?.("a[href]")) event.preventDefault();
});

// A browser storage contract, independent of whatever Node exposes as
// localStorage, so local and CI runs behave the same.
const values = new Map<string, string>();
const memoryStorage: Storage = {
  get length() {
    return values.size;
  },
  clear: () => values.clear(),
  getItem: (key) => values.get(key) ?? null,
  key: (index) => Array.from(values.keys())[index] ?? null,
  removeItem: (key) => {
    values.delete(key);
  },
  setItem: (key, value) => {
    values.set(key, String(value));
  },
};
Object.defineProperty(window, "localStorage", {
  configurable: true,
  value: memoryStorage,
});
