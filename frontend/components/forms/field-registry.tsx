"use client";

import type { FieldValues, UseFormRegister, FieldErrors, Control } from "react-hook-form";
import { Controller } from "react-hook-form";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Label } from "@/components/ui/label";

type FieldWidgetProps = {
  name: string;
  schema: Record<string, unknown>;
  register: UseFormRegister<FieldValues>;
  control: Control<FieldValues>;
  errors: FieldErrors;
  fieldConfig?: Record<string, unknown>;
};

function TextWidget({ name, schema, register, errors }: FieldWidgetProps) {
  return (
    <Input
      {...register(name)}
      placeholder={(schema.placeholder as string) || `Enter ${schema.title || name}`}
      type="text"
    />
  );
}

function TextareaWidget({ name, schema, register, errors }: FieldWidgetProps) {
  return (
    <Textarea
      {...register(name)}
      placeholder={(schema.placeholder as string) || `Enter ${schema.title || name}`}
      rows={4}
    />
  );
}

function NumberWidget({ name, schema, register, errors }: FieldWidgetProps) {
  return (
    <Input
      {...register(name, { valueAsNumber: true })}
      type="number"
      min={schema.minimum as number | undefined}
      max={schema.maximum as number | undefined}
      placeholder={(schema.placeholder as string) || `Enter ${schema.title || name}`}
    />
  );
}

function BooleanWidget({ name, schema, register, errors }: FieldWidgetProps) {
  return (
    <label className="flex items-center gap-2">
      <input type="checkbox" {...register(name)} className="h-4 w-4 rounded border" />
      <span className="text-sm">{(schema.title as string) || name}</span>
    </label>
  );
}

function SelectWidget({ name, schema, control, errors }: FieldWidgetProps) {
  const options = (schema.enum as string[]) || [];
  return (
    <Controller
      name={name}
      control={control}
      render={({ field }) => (
        <Select onValueChange={field.onChange} value={field.value || ""}>
          <SelectTrigger>
            <SelectValue placeholder={`Select ${(schema.title as string) || name}`} />
          </SelectTrigger>
          <SelectContent>
            {options.map((opt) => (
              <SelectItem key={opt} value={opt}>
                {opt}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      )}
    />
  );
}

function DateWidget({ name, schema, register, errors }: FieldWidgetProps) {
  return (
    <Input
      {...register(name)}
      type={schema.format === "date-time" ? "datetime-local" : "date"}
    />
  );
}

function EmailWidget({ name, schema, register, errors }: FieldWidgetProps) {
  return (
    <Input
      {...register(name)}
      type="email"
      placeholder={(schema.placeholder as string) || `Enter email`}
    />
  );
}

function UrlWidget({ name, schema, register, errors }: FieldWidgetProps) {
  return (
    <Input
      {...register(name)}
      type="url"
      placeholder={(schema.placeholder as string) || `Enter URL`}
    />
  );
}

function RatingWidget({ name, schema, control, errors }: FieldWidgetProps) {
  const max = (schema.maximum as number) || 5;
  return (
    <Controller
      name={name}
      control={control}
      render={({ field }) => (
        <div className="flex gap-1">
          {Array.from({ length: max }, (_, i) => i + 1).map((star) => (
            <button
              key={star}
              type="button"
              onClick={() => field.onChange(star)}
              className={`text-2xl transition-colors ${
                star <= (field.value || 0) ? "text-yellow-400" : "text-gray-300"
              }`}
            >
              ★
            </button>
          ))}
        </div>
      )}
    />
  );
}

function ScaleWidget({ name, schema, control, errors }: FieldWidgetProps) {
  const min = (schema.minimum as number) || 0;
  const max = (schema.maximum as number) || 10;
  return (
    <Controller
      name={name}
      control={control}
      render={({ field }) => (
        <div className="flex flex-col gap-2">
          <input
            type="range"
            min={min}
            max={max}
            value={field.value || min}
            onChange={(e) => field.onChange(parseInt(e.target.value))}
            className="w-full"
          />
          <div className="text-muted-foreground flex justify-between text-xs">
            <span>{min}</span>
            <span className="font-medium text-foreground">{field.value ?? min}</span>
            <span>{max}</span>
          </div>
        </div>
      )}
    />
  );
}

function FallbackWidget({ name, schema, register, errors }: FieldWidgetProps) {
  return (
    <Input
      {...register(name)}
      placeholder={`Enter ${(schema.title as string) || name}`}
    />
  );
}

// Map JSON Schema type + format/x-widget to a React component
function resolveWidget(schema: Record<string, unknown>): React.FC<FieldWidgetProps> {
  const xWidget = schema["x-widget"] as string | undefined;
  const type = schema.type as string;
  const format = schema.format as string | undefined;

  // x-widget overrides
  if (xWidget === "textarea") return TextareaWidget;
  if (xWidget === "rating") return RatingWidget;
  if (xWidget === "scale") return ScaleWidget;

  // Format-based
  if (format === "email") return EmailWidget;
  if (format === "uri") return UrlWidget;
  if (format === "date" || format === "date-time") return DateWidget;

  // Type-based
  if (type === "string" && schema.enum) return SelectWidget;
  if (type === "string") return TextWidget;
  if (type === "number" || type === "integer") return NumberWidget;
  if (type === "boolean") return BooleanWidget;

  return FallbackWidget;
}

export function DynamicField(props: FieldWidgetProps) {
  const { name, schema, errors } = props;
  const Widget = resolveWidget(schema);
  const error = errors[name];
  const title = (schema.title as string) || name.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());

  return (
    <div className="flex flex-col gap-1.5">
      <Label htmlFor={name}>{title}</Label>
      <Widget {...props} />
      {error && (
        <p className="text-sm text-red-500">{error.message as string}</p>
      )}
      {schema.description && (
        <p className="text-muted-foreground text-xs">{schema.description as string}</p>
      )}
    </div>
  );
}
