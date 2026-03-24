"use client";

import { useForm, type FieldValues } from "react-hook-form";
import { DynamicField } from "./field-registry";

type FormPreviewProps = {
  schema: Record<string, unknown>;
  formName?: string;
};

export function FormPreview({ schema, formName }: FormPreviewProps) {
  const {
    register,
    control,
    formState: { errors },
  } = useForm<FieldValues>();

  const properties = ((schema as Record<string, unknown>)?.properties ?? {}) as Record<
    string,
    Record<string, unknown>
  >;
  const required = new Set(((schema as Record<string, unknown>)?.required ?? []) as string[]);
  const fieldNames = Object.keys(properties);

  if (fieldNames.length === 0) {
    return (
      <div className="text-muted-foreground flex h-full items-center justify-center p-8 text-sm">
        Add fields to see a live preview
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-4">
      {formName && <h3 className="text-lg font-semibold">{formName}</h3>}
      {fieldNames.map((fieldName) => {
        const fieldSchema = { ...properties[fieldName] };
        if (required.has(fieldName)) {
          const title =
            (fieldSchema.title as string) ||
            fieldName.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
          fieldSchema.title = title + " *";
        }
        return (
          <DynamicField
            key={fieldName}
            name={fieldName}
            schema={fieldSchema}
            register={register}
            control={control}
            errors={errors}
          />
        );
      })}
      <div className="bg-primary text-primary-foreground cursor-not-allowed rounded-md px-4 py-2 text-center text-sm opacity-50">
        Submit (preview only)
      </div>
    </div>
  );
}
