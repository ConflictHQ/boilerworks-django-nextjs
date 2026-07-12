// Tests for multi-page splitting (#75 page breaks / pagination).
import { describe, expect, it } from "vitest";
import { splitIntoPages } from "@/components/forms/DynamicForm";

const pageBreak = (title = "") => ({ type: "string", "x-widget": "page_break", title });

describe("splitIntoPages", () => {
  it("returns a single page when there are no page breaks", () => {
    const props = { a: { type: "string" }, b: { type: "string" } };
    const pages = splitIntoPages(["a", "b"], props);
    expect(pages).toHaveLength(1);
    expect(pages[0].fieldNames).toEqual(["a", "b"]);
  });

  it("splits at page_break markers and uses their title for the next page", () => {
    const props = {
      a: { type: "string" },
      brk: pageBreak("Details"),
      b: { type: "string" },
      c: { type: "string" },
    };
    const pages = splitIntoPages(["a", "brk", "b", "c"], props);
    expect(pages).toHaveLength(2);
    expect(pages[0]).toEqual({ title: "", fieldNames: ["a"] });
    expect(pages[1]).toEqual({ title: "Details", fieldNames: ["b", "c"] });
  });

  it("drops empty pages from leading/trailing/adjacent breaks", () => {
    const props = {
      brk1: pageBreak(),
      a: { type: "string" },
      brk2: pageBreak(),
      brk3: pageBreak(),
      b: { type: "string" },
      brk4: pageBreak(),
    };
    const pages = splitIntoPages(["brk1", "a", "brk2", "brk3", "b", "brk4"], props);
    expect(pages).toHaveLength(2);
    expect(pages[0].fieldNames).toEqual(["a"]);
    expect(pages[1].fieldNames).toEqual(["b"]);
  });

  it("handles a schema of only page breaks without crashing", () => {
    const props = { brk: pageBreak() };
    const pages = splitIntoPages(["brk"], props);
    expect(pages).toHaveLength(1);
    expect(pages[0].fieldNames).toEqual([]);
  });
});
