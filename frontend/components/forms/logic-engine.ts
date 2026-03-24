/**
 * Form Logic Engine — evaluates conditional rules client-side.
 *
 * Rule format (from FormDefinition.logic_rules):
 * {
 *   condition: { field: "expense_type", op: "eq", value: "travel" },
 *   action: "show" | "hide" | "require" | "skip_to" | "set_value" | "calculate",
 *   target: "destination_city"
 * }
 *
 * Calculation format (from FormDefinition.field_config[field].calculation):
 * { op: "sum" | "avg" | "multiply" | "expression", fields: ["a", "b"], expr?: "a * b" }
 */

export type LogicCondition = {
  field: string;
  op: "eq" | "neq" | "gt" | "lt" | "gte" | "lte" | "in" | "not_in" | "contains" | "is_empty" | "is_not_empty";
  value?: unknown;
};

export type LogicRule = {
  condition: LogicCondition;
  action: "show" | "hide" | "require" | "skip_to" | "set_value" | "calculate" | "display_from";
  target: string;
  value?: unknown;
};

export type FieldVisibility = Record<string, boolean>;
export type FieldRequired = Record<string, boolean>;
export type CalculatedValues = Record<string, unknown>;

export type LogicState = {
  visibility: FieldVisibility;
  required: FieldRequired;
  calculated: CalculatedValues;
};

/**
 * Evaluate a single condition against the current form values.
 */
function evaluateCondition(condition: LogicCondition, values: Record<string, unknown>): boolean {
  const fieldValue = values[condition.field];
  const compareValue = condition.value;

  switch (condition.op) {
    case "eq":
      return fieldValue === compareValue || String(fieldValue) === String(compareValue);
    case "neq":
      return fieldValue !== compareValue && String(fieldValue) !== String(compareValue);
    case "gt":
      return Number(fieldValue) > Number(compareValue);
    case "lt":
      return Number(fieldValue) < Number(compareValue);
    case "gte":
      return Number(fieldValue) >= Number(compareValue);
    case "lte":
      return Number(fieldValue) <= Number(compareValue);
    case "in":
      return Array.isArray(compareValue) && compareValue.includes(fieldValue);
    case "not_in":
      return Array.isArray(compareValue) && !compareValue.includes(fieldValue);
    case "contains":
      return typeof fieldValue === "string" && fieldValue.includes(String(compareValue));
    case "is_empty":
      return fieldValue === undefined || fieldValue === null || fieldValue === "";
    case "is_not_empty":
      return fieldValue !== undefined && fieldValue !== null && fieldValue !== "";
    default:
      return false;
  }
}

/**
 * Evaluate a calculation against current form values.
 */
function evaluateCalculation(
  calc: { op: string; fields?: string[]; expr?: string; field?: string },
  values: Record<string, unknown>,
): unknown {
  if (calc.op === "display_from") {
    return values[calc.field ?? ""];
  }

  if (calc.op === "expression" && calc.expr) {
    try {
      // Simple expression eval — only numeric payload values
      const fn = new Function(
        ...Object.keys(values).filter((k) => typeof values[k] === "number"),
        `return ${calc.expr}`,
      );
      const numericValues = Object.entries(values)
        .filter(([, v]) => typeof v === "number")
        .map(([, v]) => v);
      return fn(...numericValues);
    } catch {
      return undefined;
    }
  }

  const fields = calc.fields ?? [];
  const nums = fields.map((f) => Number(values[f])).filter((n) => !isNaN(n));
  if (nums.length === 0) return undefined;

  switch (calc.op) {
    case "sum":
      return nums.reduce((a, b) => a + b, 0);
    case "avg":
      return nums.reduce((a, b) => a + b, 0) / nums.length;
    case "min":
      return Math.min(...nums);
    case "max":
      return Math.max(...nums);
    case "multiply":
      return nums.reduce((a, b) => a * b, 1);
    case "subtract":
      return nums.length >= 2 ? nums[0] - nums[1] : undefined;
    case "divide":
      return nums.length >= 2 && nums[1] !== 0 ? nums[0] / nums[1] : undefined;
    case "percentage":
      return nums.length >= 2 && nums[1] !== 0 ? (nums[0] / nums[1]) * 100 : undefined;
    default:
      return undefined;
  }
}

/**
 * Evaluate all logic rules against current form values.
 * Returns visibility, required state, and calculated values for each field.
 */
export function evaluateLogicRules(
  rules: LogicRule[],
  fieldConfig: Record<string, Record<string, unknown>>,
  values: Record<string, unknown>,
  allFieldNames: string[],
): LogicState {
  // Start with all fields visible, only schema-required fields required
  const visibility: FieldVisibility = {};
  const required: FieldRequired = {};
  const calculated: CalculatedValues = {};

  for (const name of allFieldNames) {
    visibility[name] = true;
    required[name] = false;
  }

  // Apply logic rules
  for (const rule of rules) {
    const conditionMet = evaluateCondition(rule.condition, values);

    switch (rule.action) {
      case "show":
        if (conditionMet) visibility[rule.target] = true;
        else visibility[rule.target] = false;
        break;
      case "hide":
        if (conditionMet) visibility[rule.target] = false;
        break;
      case "require":
        if (conditionMet) required[rule.target] = true;
        break;
      case "set_value":
        if (conditionMet && rule.value !== undefined) {
          calculated[rule.target] = rule.value;
        }
        break;
      case "calculate": {
        const config = fieldConfig[rule.target]?.calculation as
          | { op: string; fields?: string[]; expr?: string; field?: string }
          | undefined;
        if (config) {
          calculated[rule.target] = evaluateCalculation(config, values);
        }
        break;
      }
      case "display_from": {
        calculated[rule.target] = values[rule.condition.field];
        break;
      }
    }
  }

  // Also evaluate calculations defined in field_config (not just rules)
  for (const [fieldName, config] of Object.entries(fieldConfig)) {
    const calc = config.calculation as
      | { op: string; fields?: string[]; expr?: string; field?: string }
      | undefined;
    if (calc && !(fieldName in calculated)) {
      calculated[fieldName] = evaluateCalculation(calc, values);
    }
  }

  return { visibility, required, calculated };
}
