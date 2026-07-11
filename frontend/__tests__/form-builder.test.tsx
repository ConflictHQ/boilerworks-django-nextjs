// Regression guards for the two critical Form Builder bugs from #71,
// fixed in 8155c1c (PR #72):
//   1. "Add Field" (and every other builder button) must not submit an
//      enclosing form — all buttons carry type="button".
//   2. The field-type Select must show the current type's label on first
//      render (explicit children on SelectValue), never render empty.
import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import { FormBuilder } from "@/components/forms/FormBuilder";

const SCHEMA = {
  type: "object",
  properties: { name: { type: "string", title: "Name" } },
  required: ["name"],
};

describe("FormBuilder (#71 critical bugs)", () => {
  it("Add Field does not submit an enclosing form and appends a field", () => {
    const onSubmit = vi.fn((e: React.FormEvent) => e.preventDefault());
    render(
      <form onSubmit={onSubmit}>
        <FormBuilder schema={SCHEMA} onSave={() => {}} />
      </form>
    );

    fireEvent.click(screen.getByRole("button", { name: /add field/i }));

    expect(onSubmit).not.toHaveBeenCalled();
    // The new field row appears (default title "Field 2" after the existing one)
    expect(screen.getByDisplayValue("Field 2")).toBeTruthy();
  });

  it("every button inside the builder has an explicit non-submit type", () => {
    const { container } = render(
      <form>
        <FormBuilder schema={SCHEMA} onSave={() => {}} />
      </form>
    );
    const buttons = container.querySelectorAll("button");
    expect(buttons.length).toBeGreaterThan(0);
    for (const b of buttons) {
      expect(b.getAttribute("type")).toBe("button");
    }
  });

  it("field type Select shows the current type label on first render", () => {
    const { container } = render(<FormBuilder schema={SCHEMA} onSave={() => {}} />);
    // The schema's single field is a plain string -> type "text", label "Text".
    // The trigger's SelectValue must render it immediately (bug 2 rendered empty).
    const value = container.querySelector('[data-slot="select-value"]');
    expect(value?.textContent).toBe("Text");
  });
});
