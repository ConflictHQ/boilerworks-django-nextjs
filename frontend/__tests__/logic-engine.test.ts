import { describe, expect, it } from "vitest";
import { evaluateLogicRules, type LogicRule } from "@/components/forms/logic-engine";

const FIELDS = ["expense_type", "destination_city", "amount", "tax", "total"];

describe("evaluateLogicRules", () => {
  it("defaults every field to visible and not required", () => {
    const state = evaluateLogicRules([], {}, {}, FIELDS);
    for (const name of FIELDS) {
      expect(state.visibility[name]).toBe(true);
      expect(state.required[name]).toBe(false);
    }
    expect(state.calculated).toEqual({});
  });

  it("shows and hides targets based on eq conditions", () => {
    const rules: LogicRule[] = [
      {
        condition: { field: "expense_type", op: "eq", value: "travel" },
        action: "show",
        target: "destination_city",
      },
    ];
    const shown = evaluateLogicRules(rules, {}, { expense_type: "travel" }, FIELDS);
    expect(shown.visibility.destination_city).toBe(true);

    const hidden = evaluateLogicRules(rules, {}, { expense_type: "meals" }, FIELDS);
    expect(hidden.visibility.destination_city).toBe(false);
  });

  it("marks targets required when the condition is met", () => {
    const rules: LogicRule[] = [
      {
        condition: { field: "amount", op: "gt", value: 100 },
        action: "require",
        target: "destination_city",
      },
    ];
    const state = evaluateLogicRules(rules, {}, { amount: 150 }, FIELDS);
    expect(state.required.destination_city).toBe(true);
  });

  it("computes sum calculations from field_config", () => {
    const fieldConfig = {
      total: { calculation: { op: "sum", fields: ["amount", "tax"] } },
    };
    const state = evaluateLogicRules([], fieldConfig, { amount: 100, tax: 8 }, FIELDS);
    expect(state.calculated.total).toBe(108);
  });
});
