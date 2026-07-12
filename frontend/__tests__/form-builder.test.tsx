// Regression guards for the two critical Form Builder bugs from #71,
// fixed in 8155c1c (PR #72):
//   1. "Add Field" (and every other builder button) must not submit an
//      enclosing form — all buttons carry type="button".
//   2. The field-type Select must show the current type's label on first
//      render (explicit children on SelectValue), never render empty.
import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, within } from "@testing-library/react";
import {
  FormBuilder,
  fieldsToSchema,
  schemaToFields,
  type FieldDef,
} from "@/components/forms/FormBuilder";

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

describe("FormBuilder conditional logic editor (#71 UX)", () => {
  it("adds a rule and embeds it in the saved schema as x-logic-rules", () => {
    const onSave = vi.fn();
    const { container } = render(<FormBuilder schema={SCHEMA} onSave={onSave} />);
    const scope = within(container as HTMLElement);

    fireEvent.click(scope.getByRole("button", { name: /add rule/i }));
    fireEvent.click(scope.getByRole("button", { name: /save schema/i }));

    const saved = onSave.mock.calls[0][0] as Record<string, unknown>;
    const rules = saved["x-logic-rules"] as Array<Record<string, unknown>>;
    expect(rules).toHaveLength(1);
    expect(rules[0]).toMatchObject({
      condition: { field: "name", op: "eq" },
      action: "show",
      target: "name",
    });
  });

  it("restores existing x-logic-rules from the schema and can remove them", () => {
    const onSave = vi.fn();
    const schemaWithRules = {
      ...SCHEMA,
      "x-logic-rules": [
        { condition: { field: "name", op: "is_empty" }, action: "require", target: "name" },
      ],
    };
    const { container } = render(<FormBuilder schema={schemaWithRules} onSave={onSave} />);
    const scope = within(container as HTMLElement);

    fireEvent.click(scope.getByLabelText(/remove rule 1/i));
    fireEvent.click(scope.getByRole("button", { name: /save schema/i }));

    const saved = onSave.mock.calls[0][0] as Record<string, unknown>;
    expect(saved["x-logic-rules"]).toBeUndefined();
  });
});

describe("FormBuilder Expand All / Collapse All (#71 UX)", () => {
  it("Expand All opens every field's config panel; Collapse All closes them", () => {
    const { container } = render(<FormBuilder schema={SCHEMA} onSave={() => {}} />);
    const scope = within(container as HTMLElement);

    // Config panel content (Field name slug label) is hidden until expanded.
    expect(scope.queryByText("Field name (slug)")).toBeNull();

    fireEvent.click(scope.getByRole("button", { name: /expand all/i }));
    expect(scope.getByText("Field name (slug)")).toBeTruthy();

    fireEvent.click(scope.getByRole("button", { name: /collapse all/i }));
    expect(scope.queryByText("Field name (slug)")).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// Schema serialization round-trip (#71 per-type config, #75 widget config)
// ---------------------------------------------------------------------------

function makeField(overrides: Partial<FieldDef>): FieldDef {
  return {
    id: "field-test",
    name: "test_field",
    type: "text",
    title: "Test Field",
    required: false,
    description: "",
    placeholder: "",
    defaultValue: "",
    width: "full",
    options: [],
    min: "",
    max: "",
    step: "",
    prefix: "",
    suffix: "",
    minLength: "",
    maxLength: "",
    pattern: "",
    acceptedFileTypes: "",
    maxFileSize: "",
    allowMultiple: false,
    scaleMinLabel: "",
    scaleMaxLabel: "",
    categories: [],
    imageSrc: "",
    innerFields: [],
    ...overrides,
  };
}

function roundTrip(field: FieldDef): FieldDef {
  return schemaToFields(fieldsToSchema([field]))[0];
}

describe("fieldsToSchema serialization", () => {
  it("radio serializes x-widget and enum options", () => {
    const schema = fieldsToSchema([
      makeField({ type: "radio", name: "choice", options: ["A", "B"] }),
    ]);
    const prop = (schema.properties as Record<string, Record<string, unknown>>).choice;
    expect(prop["x-widget"]).toBe("radio");
    expect(prop.enum).toEqual(["A", "B"]);
  });

  it("time serializes format + x-widget", () => {
    const schema = fieldsToSchema([makeField({ type: "time", name: "at" })]);
    const prop = (schema.properties as Record<string, Record<string, unknown>>).at;
    expect(prop.format).toBe("time");
    expect(prop["x-widget"]).toBe("time");
  });

  it("display types (text_block, section_header, page_break, image, embed) keep x-widget", () => {
    for (const type of ["text_block", "section_header", "page_break", "image", "embed"]) {
      const schema = fieldsToSchema([makeField({ type, name: "d" })]);
      const prop = (schema.properties as Record<string, Record<string, unknown>>).d;
      expect(prop["x-widget"]).toBe(type);
    }
  });

  it("number config (step, prefix, suffix, default) is serialized", () => {
    const schema = fieldsToSchema([
      makeField({
        type: "number",
        name: "amount",
        min: "0",
        max: "100",
        step: "0.5",
        prefix: "$",
        suffix: "USD",
        defaultValue: "5",
      }),
    ]);
    const prop = (schema.properties as Record<string, Record<string, unknown>>).amount;
    expect(prop.minimum).toBe(0);
    expect(prop.maximum).toBe(100);
    expect(prop["x-step"]).toBe(0.5);
    expect(prop["x-prefix"]).toBe("$");
    expect(prop["x-suffix"]).toBe("USD");
    expect(prop.default).toBe(5);
  });

  it("repeatable serializes inner fields as items object schema", () => {
    const schema = fieldsToSchema([
      makeField({
        type: "repeatable",
        name: "rows",
        innerFields: [
          { name: "item", title: "Item", type: "text" },
          { name: "qty", title: "Qty", type: "integer" },
        ],
      }),
    ]);
    const prop = (schema.properties as Record<string, Record<string, unknown>>).rows;
    expect(prop["x-widget"]).toBe("repeatable");
    const items = prop.items as { type: string; properties: Record<string, unknown> };
    expect(items.type).toBe("object");
    expect(Object.keys(items.properties)).toEqual(["item", "qty"]);
  });
});

describe("schema round-trip (edit an existing form without losing config)", () => {
  it("scale keeps endpoint labels and bounds", () => {
    const out = roundTrip(
      makeField({
        type: "scale",
        name: "mood",
        min: "1",
        max: "7",
        scaleMinLabel: "Not at all",
        scaleMaxLabel: "Extremely",
      })
    );
    expect(out.type).toBe("scale");
    expect(out.min).toBe("1");
    expect(out.max).toBe("7");
    expect(out.scaleMinLabel).toBe("Not at all");
    expect(out.scaleMaxLabel).toBe("Extremely");
  });

  it("file keeps accept, max size, and multiple", () => {
    const out = roundTrip(
      makeField({
        type: "file",
        name: "docs",
        acceptedFileTypes: ".pdf,.png",
        maxFileSize: "10",
        allowMultiple: true,
      })
    );
    expect(out.type).toBe("file");
    expect(out.acceptedFileTypes).toBe(".pdf,.png");
    expect(out.maxFileSize).toBe("10");
    expect(out.allowMultiple).toBe(true);
  });

  it("percentage split keeps categories", () => {
    const out = roundTrip(
      makeField({ type: "percentage_split", name: "split", categories: ["Rent", "Food"] })
    );
    expect(out.type).toBe("percentage_split");
    expect(out.categories).toEqual(["Rent", "Food"]);
  });

  it("text keeps validation config and width", () => {
    const out = roundTrip(
      makeField({
        type: "text",
        name: "code",
        minLength: "2",
        maxLength: "8",
        pattern: "^[A-Z]+$",
        placeholder: "ABC",
        defaultValue: "AA",
        width: "half",
      })
    );
    expect(out.minLength).toBe("2");
    expect(out.maxLength).toBe("8");
    expect(out.pattern).toBe("^[A-Z]+$");
    expect(out.placeholder).toBe("ABC");
    expect(out.defaultValue).toBe("AA");
    expect(out.width).toBe("half");
  });

  it("repeatable keeps inner fields", () => {
    const out = roundTrip(
      makeField({
        type: "repeatable",
        name: "rows",
        innerFields: [
          { name: "item", title: "Item", type: "text" },
          { name: "when", title: "When", type: "date" },
        ],
      })
    );
    expect(out.type).toBe("repeatable");
    expect(out.innerFields).toEqual([
      { name: "item", title: "Item", type: "text" },
      { name: "when", title: "When", type: "date" },
    ]);
  });

  it("radio, select, and multi-select keep options", () => {
    for (const type of ["radio", "select", "multi_select"]) {
      const out = roundTrip(makeField({ type, name: "opts", options: ["x", "y"] }));
      expect(out.type).toBe(type);
      expect(out.options).toEqual(["x", "y"]);
    }
  });

  it("image and embed keep their source URL", () => {
    for (const type of ["image", "embed"]) {
      const out = roundTrip(makeField({ type, name: "media", imageSrc: "https://x.test/a.png" }));
      expect(out.type).toBe(type);
      expect(out.imageSrc).toBe("https://x.test/a.png");
    }
  });
});
