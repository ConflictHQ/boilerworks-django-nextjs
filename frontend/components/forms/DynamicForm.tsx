"use client";

import { useEffect, useMemo, useState } from "react";
import { useForm, useWatch, type FieldValues } from "react-hook-form";
import {
  Loader2Icon,
  SendIcon,
  CheckCircle2Icon,
  ChevronLeftIcon,
  ChevronRightIcon,
} from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { useFormDefinition, useSubmitForm } from "@/graphql/forms/forms.hooks";
import { DynamicField, fieldWidthClass } from "./field-registry";
import { evaluateLogicRules, type LogicRule, type LogicState } from "./logic-engine";

type DynamicFormProps = {
  slug: string;
  onSuccess?: (submissionId: string) => void;
};

export type FormPage = {
  /** Title of the page_break field that started this page ("" for the first page). */
  title: string;
  fieldNames: string[];
};

/**
 * Split a form's fields into pages at page_break markers.
 * The page_break field itself is consumed as the separator; its title
 * becomes the next page's heading. Exported for tests.
 */
export function splitIntoPages(
  fieldNames: string[],
  properties: Record<string, Record<string, unknown>>
): FormPage[] {
  const pages: FormPage[] = [{ title: "", fieldNames: [] }];
  for (const name of fieldNames) {
    if (properties[name]?.["x-widget"] === "page_break") {
      pages.push({ title: (properties[name].title as string) || "", fieldNames: [] });
    } else {
      pages[pages.length - 1].fieldNames.push(name);
    }
  }
  // Drop empty pages (e.g. a trailing page break with nothing after it)
  const nonEmpty = pages.filter((p) => p.fieldNames.length > 0);
  return nonEmpty.length > 0 ? nonEmpty : [{ title: "", fieldNames: [] }];
}

export function DynamicForm({ slug, onSuccess }: DynamicFormProps) {
  const { form: formDef, loading, error } = useFormDefinition(slug);
  const [submitForm] = useSubmitForm();
  const [submitted, setSubmitted] = useState(false);

  const {
    register,
    control,
    handleSubmit,
    setError,
    setValue,
    reset,
    trigger,
    formState: { errors, isSubmitting },
  } = useForm<FieldValues>();

  const [pageIndex, setPageIndex] = useState(0);

  // ALL HOOKS MUST BE ABOVE ANY EARLY RETURNS
  const watchedValues = useWatch({ control });

  const schema = (formDef?.schema ?? { properties: {}, required: [] }) as {
    type?: string;
    properties?: Record<string, Record<string, unknown>>;
    required?: string[];
  };
  const properties = schema.properties || {};
  const schemaRequired = new Set(schema.required || []);
  const fieldNames = Object.keys(properties);

  // Rules come from the backend logicRules field, plus any embedded in the
  // schema by the builder's logic editor (x-logic-rules — the create/update
  // mutation only accepts `schema`, so the builder persists rules inside it).
  const backendRules = ((formDef as Record<string, unknown> | null)?.logicRules ??
    []) as LogicRule[];
  const schemaRules = ((schema as Record<string, unknown>)["x-logic-rules"] ?? []) as LogicRule[];
  const logicRules = [...backendRules, ...schemaRules];
  const fieldConfig = ((formDef as Record<string, unknown> | null)?.fieldConfig ?? {}) as Record<
    string,
    Record<string, unknown>
  >;

  const watchedValuesKey = JSON.stringify(watchedValues);
  const logicRulesKey = JSON.stringify(logicRules);
  const fieldConfigKey = JSON.stringify(fieldConfig);
  const fieldNamesKey = fieldNames.join(",");

  const logicState: LogicState = useMemo(
    () => evaluateLogicRules(logicRules, fieldConfig, watchedValues ?? {}, fieldNames),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [watchedValuesKey, logicRulesKey, fieldConfigKey, fieldNamesKey]
  );

  const pages = useMemo(
    () => splitIntoPages(fieldNames, properties),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [fieldNamesKey]
  );
  const multiPage = pages.length > 1;
  const safePageIndex = Math.min(pageIndex, pages.length - 1);
  const currentPage = pages[safePageIndex];
  const isLastPage = safePageIndex === pages.length - 1;

  useEffect(() => {
    for (const [field, value] of Object.entries(logicState.calculated)) {
      if (value !== undefined) {
        setValue(field, value);
      }
    }
  }, [logicState.calculated, setValue]);

  // Pre-fill schema `default` values once the definition loads.
  useEffect(() => {
    if (!formDef) return;
    const props = ((formDef.schema as Record<string, unknown>)?.properties ?? {}) as Record<
      string,
      Record<string, unknown>
    >;
    const defaults: FieldValues = {};
    for (const [fieldName, def] of Object.entries(props)) {
      if (def.default !== undefined) defaults[fieldName] = def.default;
    }
    if (Object.keys(defaults).length > 0) reset(defaults);
  }, [formDef, reset]);

  // NOW safe to do early returns
  if (loading) {
    return (
      <div className="flex items-center justify-center p-12">
        <Loader2Icon className="text-muted-foreground h-6 w-6 animate-spin" />
      </div>
    );
  }

  if (error || !formDef) {
    return (
      <div className="rounded-md bg-red-50 p-4 text-red-800">
        {error
          ? `Error loading form: ${error.message}`
          : `Form "${slug}" not found or not published.`}
      </div>
    );
  }

  if (submitted) {
    return (
      <Card className="flex flex-col items-center gap-4 p-8 text-center">
        <CheckCircle2Icon className="h-12 w-12 text-green-500" />
        <h2 className="text-xl font-semibold">Submitted!</h2>
        <p className="text-muted-foreground">
          Your response to &quot;{formDef.name}&quot; has been recorded.
        </p>
      </Card>
    );
  }

  // Display-only widget types that should not be included in payload
  const DISPLAY_WIDGETS = new Set(["text_block", "section_header", "page_break", "image", "embed"]);

  const onSubmit = async (data: FieldValues) => {
    const payload: Record<string, unknown> = {};
    for (const [key, value] of Object.entries(data)) {
      // Skip hidden fields
      if (logicState.visibility[key] === false) continue;
      // Skip display-only widgets
      const fieldSchema = properties[key];
      if (fieldSchema && DISPLAY_WIDGETS.has(fieldSchema["x-widget"] as string)) continue;
      // Skip File objects (can't serialize to JSON)
      if (value instanceof File || (Array.isArray(value) && value[0] instanceof File)) continue;

      if (value !== "" && value !== undefined && value !== null) {
        payload[key] = value;
      } else if (schemaRequired.has(key) || logicState.required[key]) {
        payload[key] = value;
      }
    }

    const { data: result } = await submitForm({
      variables: { slug, payload },
    });

    if (result?.submitForm.ok) {
      setSubmitted(true);
      toast.success("Form submitted", { description: formDef.name });
      if (result.submitForm.submissionId && onSuccess) {
        onSuccess(result.submitForm.submissionId);
      }
    } else if (result?.submitForm.errors) {
      for (const err of result.submitForm.errors) {
        setError(err.field || "root", {
          type: "server",
          message: err.messages.join(", "),
        });
      }
      toast.error("Validation failed", { description: "Please fix the errors below." });
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-6">
      <div>
        <h2 className="text-lg font-semibold">{formDef.name}</h2>
        {formDef.description && (
          <p className="text-muted-foreground mt-1 text-sm">{formDef.description}</p>
        )}
      </div>
      <Separator />

      {multiPage && (
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium">
            {currentPage.title || `Page ${safePageIndex + 1}`}
          </span>
          <span className="text-muted-foreground text-xs">
            Page {safePageIndex + 1} of {pages.length}
          </span>
        </div>
      )}

      <div className="grid grid-cols-6 gap-4">
        {currentPage.fieldNames.map((fieldName) => {
          const isHidden = logicState.visibility[fieldName] === false;
          const fieldSchema = { ...properties[fieldName] };
          const widthClass = fieldWidthClass(fieldSchema);
          const isRequired = schemaRequired.has(fieldName) || logicState.required[fieldName];
          if (isRequired) {
            fieldSchema._required = true;
            const title =
              (fieldSchema.title as string) ||
              fieldName.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
            fieldSchema.title = title + " *";
          }

          if (
            fieldName in logicState.calculated &&
            logicState.calculated[fieldName] !== undefined
          ) {
            return (
              <div
                key={fieldName}
                className={`flex flex-col gap-1.5 ${widthClass} ${isHidden ? "hidden" : ""}`}
              >
                <label className="text-sm font-medium">
                  {(fieldSchema.title as string) || fieldName}
                </label>
                <div className="bg-muted rounded-md px-3 py-2 text-sm">
                  {String(logicState.calculated[fieldName])}
                </div>
              </div>
            );
          }

          return (
            <div key={fieldName} className={`${widthClass} ${isHidden ? "hidden" : ""}`}>
              <DynamicField
                name={fieldName}
                schema={fieldSchema}
                register={register}
                control={control}
                errors={errors}
              />
            </div>
          );
        })}
      </div>

      {errors.root && (
        <div className="rounded-md bg-red-50 p-3 text-sm text-red-800">
          {errors.root.message as string}
        </div>
      )}

      <div className="flex items-center gap-2">
        {multiPage && safePageIndex > 0 && (
          <Button type="button" variant="outline" onClick={() => setPageIndex(safePageIndex - 1)}>
            <ChevronLeftIcon className="mr-1 h-4 w-4" /> Previous
          </Button>
        )}
        {multiPage && !isLastPage && (
          <Button
            type="button"
            onClick={async () => {
              // Validate only the visible fields on this page before advancing.
              const visibleFields = currentPage.fieldNames.filter(
                (f) => logicState.visibility[f] !== false
              );
              const ok = await trigger(visibleFields);
              if (ok) setPageIndex(safePageIndex + 1);
            }}
          >
            Next <ChevronRightIcon className="ml-1 h-4 w-4" />
          </Button>
        )}
        {(!multiPage || isLastPage) && (
          <Button type="submit" disabled={isSubmitting}>
            {isSubmitting ? (
              <Loader2Icon className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <SendIcon className="mr-2 h-4 w-4" />
            )}
            Submit
          </Button>
        )}
      </div>
    </form>
  );
}
