// Tests for the #75 field-widget additions: percentage split (sum-to-100),
// repeatable rows, file size limits, and the x-width layout helper.
import { describe, expect, it } from "vitest";
import { fireEvent, render, within } from "@testing-library/react";
import { useForm, type FieldValues } from "react-hook-form";
import {
  DynamicField,
  fieldWidthClass,
  partitionFilesBySize,
  sumSplit,
} from "@/components/forms/field-registry";

function Harness({ schema, name = "f" }: { schema: Record<string, unknown>; name?: string }) {
  const {
    register,
    control,
    formState: { errors },
  } = useForm<FieldValues>();
  return (
    <DynamicField
      name={name}
      schema={schema}
      register={register}
      control={control}
      errors={errors}
    />
  );
}

describe("sumSplit", () => {
  it("sums numeric values and ignores blanks/NaN", () => {
    expect(sumSplit({ a: 40, b: 60 })).toBe(100);
    expect(sumSplit({ a: 40, b: "", c: "20" })).toBe(60);
    expect(sumSplit(undefined)).toBe(0);
  });
});

describe("partitionFilesBySize", () => {
  const small = new File(["x"], "small.txt");
  const big = new File([new ArrayBuffer(2 * 1024 * 1024)], "big.bin");

  it("accepts everything when no limit is set", () => {
    const { accepted, rejected } = partitionFilesBySize([small, big], undefined);
    expect(accepted).toHaveLength(2);
    expect(rejected).toHaveLength(0);
  });

  it("rejects files over the limit", () => {
    const { accepted, rejected } = partitionFilesBySize([small, big], 1);
    expect(accepted.map((f) => f.name)).toEqual(["small.txt"]);
    expect(rejected.map((f) => f.name)).toEqual(["big.bin"]);
  });
});

describe("fieldWidthClass", () => {
  it("maps x-width to grid column spans", () => {
    expect(fieldWidthClass({})).toBe("col-span-6");
    expect(fieldWidthClass({ "x-width": "half" })).toBe("col-span-6 md:col-span-3");
    expect(fieldWidthClass({ "x-width": "third" })).toBe("col-span-6 md:col-span-2");
  });
});

describe("PercentageSplitWidget", () => {
  const schema = {
    type: "object",
    "x-widget": "percentage_split",
    title: "Budget",
    "x-categories": ["Rent", "Food"],
  };

  it("renders an input per category and flags an unbalanced total", () => {
    const { container } = render(<Harness schema={schema} name="budget" />);
    const scope = within(container as HTMLElement);
    expect(scope.getByText("Rent")).toBeTruthy();
    expect(scope.getByText("Food")).toBeTruthy();
    expect(scope.getByText(/must equal 100%/)).toBeTruthy();
  });

  it("shows a balanced total once values sum to 100", () => {
    const { container } = render(<Harness schema={schema} name="budget" />);
    const inputs = (container as HTMLElement).querySelectorAll('input[type="number"]');
    fireEvent.change(inputs[0], { target: { value: "40" } });
    fireEvent.change(inputs[1], { target: { value: "60" } });
    expect(within(container as HTMLElement).getByText(/Total: 100%/)).toBeTruthy();
    expect(within(container as HTMLElement).queryByText(/must equal 100%/)).toBeNull();
  });
});

describe("RepeatableWidget", () => {
  const schema = {
    type: "array",
    "x-widget": "repeatable",
    title: "Line Items",
    items: {
      type: "object",
      properties: {
        item: { type: "string", title: "Item" },
        qty: { type: "integer", title: "Qty" },
      },
    },
  };

  it("adds and removes rows", () => {
    const { container } = render(<Harness schema={schema} name="lines" />);
    const scope = within(container as HTMLElement);

    // No rows initially
    expect(scope.queryByLabelText(/remove row 1/i)).toBeNull();

    fireEvent.click(scope.getByRole("button", { name: /add row/i }));
    fireEvent.click(scope.getByRole("button", { name: /add row/i }));
    expect(scope.getByLabelText(/remove row 2/i)).toBeTruthy();

    fireEvent.click(scope.getByLabelText(/remove row 1/i));
    expect(scope.queryByLabelText(/remove row 2/i)).toBeNull();
    expect(scope.getByLabelText(/remove row 1/i)).toBeTruthy();
  });

  it("renders a column per inner field", () => {
    const { container } = render(<Harness schema={schema} name="lines" />);
    const scope = within(container as HTMLElement);
    fireEvent.click(scope.getByRole("button", { name: /add row/i }));
    expect(scope.getByText("Item")).toBeTruthy();
    expect(scope.getByText("Qty")).toBeTruthy();
  });
});
