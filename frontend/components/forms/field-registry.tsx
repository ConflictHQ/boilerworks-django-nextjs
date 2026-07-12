"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import type { FieldValues, UseFormRegister, FieldErrors, Control } from "react-hook-form";
import { Controller } from "react-hook-form";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { UploadIcon, XIcon } from "lucide-react";

type FieldWidgetProps = {
  name: string;
  schema: Record<string, unknown>;
  register: UseFormRegister<FieldValues>;
  control: Control<FieldValues>;
  errors: FieldErrors;
  fieldConfig?: Record<string, unknown>;
};

// ---------------------------------------------------------------------------
// Basic inputs
// ---------------------------------------------------------------------------

function TextWidget({ name, schema, register }: FieldWidgetProps) {
  return (
    <Input
      {...register(name)}
      placeholder={(schema.placeholder as string) || `Enter ${schema.title || name}`}
      type="text"
    />
  );
}

function TextareaWidget({ name, schema, register }: FieldWidgetProps) {
  return (
    <Textarea
      {...register(name)}
      placeholder={(schema.placeholder as string) || `Enter ${schema.title || name}`}
      rows={4}
    />
  );
}

function NumberWidget({ name, schema, register }: FieldWidgetProps) {
  const prefix = schema["x-prefix"] as string | undefined;
  const suffix = schema["x-suffix"] as string | undefined;
  const input = (
    <Input
      {...register(name, { valueAsNumber: true })}
      type="number"
      min={schema.minimum as number | undefined}
      max={schema.maximum as number | undefined}
      step={schema["x-step"] as number | undefined}
      placeholder={(schema.placeholder as string) || `Enter ${schema.title || name}`}
    />
  );
  if (!prefix && !suffix) return input;
  return (
    <div className="flex items-center gap-2">
      {prefix && <span className="text-muted-foreground text-sm">{prefix}</span>}
      {input}
      {suffix && <span className="text-muted-foreground text-sm">{suffix}</span>}
    </div>
  );
}

function BooleanWidget({ name, schema, register }: FieldWidgetProps) {
  return (
    <label className="flex items-center gap-2">
      <input type="checkbox" {...register(name)} className="h-4 w-4 rounded border" />
      <span className="text-sm">{(schema.title as string) || name}</span>
    </label>
  );
}

function EmailWidget({ name, schema, register }: FieldWidgetProps) {
  return (
    <Input
      {...register(name)}
      type="email"
      placeholder={(schema.placeholder as string) || "Enter email"}
    />
  );
}

function UrlWidget({ name, schema, register }: FieldWidgetProps) {
  return (
    <Input
      {...register(name)}
      type="url"
      placeholder={(schema.placeholder as string) || "Enter URL"}
    />
  );
}

// ---------------------------------------------------------------------------
// Date / Time
// ---------------------------------------------------------------------------

function DateWidget({ name, schema, register }: FieldWidgetProps) {
  const xWidget = schema["x-widget"] as string | undefined;
  const format = schema.format as string | undefined;
  let inputType = "date";
  if (xWidget === "time" || format === "time") inputType = "time";
  else if (xWidget === "datetime" || format === "date-time") inputType = "datetime-local";
  return <Input {...register(name)} type={inputType} />;
}

// ---------------------------------------------------------------------------
// Select / Radio / Multi-select
// ---------------------------------------------------------------------------

function SelectWidget({ name, schema, control }: FieldWidgetProps) {
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

function RadioWidget({ name, schema, control }: FieldWidgetProps) {
  const options = (schema.enum as string[]) || [];
  return (
    <Controller
      name={name}
      control={control}
      render={({ field }) => (
        <div className="flex flex-col gap-2">
          {options.map((opt) => (
            <label key={opt} className="flex cursor-pointer items-center gap-2">
              <input
                type="radio"
                value={opt}
                checked={field.value === opt}
                onChange={() => field.onChange(opt)}
                className="h-4 w-4"
              />
              <span className="text-sm">{opt}</span>
            </label>
          ))}
        </div>
      )}
    />
  );
}

function MultiSelectWidget({ name, schema, control }: FieldWidgetProps) {
  const items = (schema.items as Record<string, unknown>) || {};
  const options = (items.enum as string[]) || (schema.enum as string[]) || [];
  return (
    <Controller
      name={name}
      control={control}
      defaultValue={[]}
      render={({ field }) => {
        const selected: string[] = field.value || [];
        const toggle = (opt: string) => {
          if (selected.includes(opt)) field.onChange(selected.filter((s: string) => s !== opt));
          else field.onChange([...selected, opt]);
        };
        return (
          <div className="flex flex-col gap-2 rounded-md border p-3">
            {options.map((opt) => (
              <label key={opt} className="flex cursor-pointer items-center gap-2">
                <input
                  type="checkbox"
                  checked={selected.includes(opt)}
                  onChange={() => toggle(opt)}
                  className="h-4 w-4 rounded"
                />
                <span className="text-sm">{opt}</span>
              </label>
            ))}
            {options.length === 0 && (
              <span className="text-muted-foreground text-xs">No options defined</span>
            )}
          </div>
        );
      }}
    />
  );
}

// ---------------------------------------------------------------------------
// Rating / Scale
// ---------------------------------------------------------------------------

function RatingWidget({ name, schema, control }: FieldWidgetProps) {
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
              className={`text-2xl transition-colors ${star <= (field.value || 0) ? "text-yellow-400" : "text-gray-300"}`}
            >
              ★
            </button>
          ))}
        </div>
      )}
    />
  );
}

function ScaleWidget({ name, schema, control }: FieldWidgetProps) {
  const min = (schema.minimum as number) || 0;
  const max = (schema.maximum as number) || 10;
  const minLabel = (schema["x-min-label"] as string) || "";
  const maxLabel = (schema["x-max-label"] as string) || "";
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
            <span>{minLabel || min}</span>
            <span className="text-foreground font-medium">{field.value ?? min}</span>
            <span>{maxLabel || max}</span>
          </div>
        </div>
      )}
    />
  );
}

// ---------------------------------------------------------------------------
// File upload (drag & drop)
// ---------------------------------------------------------------------------

/**
 * Filter incoming files against the widget's max-size limit.
 * Exported for tests.
 */
export function partitionFilesBySize(
  files: File[],
  maxSizeMb: number | undefined
): { accepted: File[]; rejected: File[] } {
  if (!maxSizeMb || maxSizeMb <= 0) return { accepted: files, rejected: [] };
  const limit = maxSizeMb * 1024 * 1024;
  const accepted: File[] = [];
  const rejected: File[] = [];
  for (const f of files) (f.size <= limit ? accepted : rejected).push(f);
  return { accepted, rejected };
}

function FilePreviewThumb({ file }: { file: File }) {
  const url = useMemo(
    () => (file.type.startsWith("image/") ? URL.createObjectURL(file) : null),
    [file]
  );
  useEffect(() => {
    return () => {
      if (url) URL.revokeObjectURL(url);
    };
  }, [url]);
  if (!url) return null;
  // eslint-disable-next-line @next/next/no-img-element -- blob object URL preview; next/image cannot optimize it
  return <img src={url} alt={file.name} className="h-8 w-8 rounded object-cover" />;
}

function FileWidget({ name, schema, control }: FieldWidgetProps) {
  const [dragOver, setDragOver] = useState(false);
  const [sizeError, setSizeError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const accept = (schema["x-accept"] as string) || "";
  const maxSizeMb = schema["x-max-size-mb"] as number | undefined;
  const multiple = schema["x-multiple"] !== false; // default true for backwards compat

  return (
    <Controller
      name={name}
      control={control}
      render={({ field }) => {
        const files: File[] = field.value || [];
        const handleFiles = (fileList: FileList) => {
          const { accepted, rejected } = partitionFilesBySize(Array.from(fileList), maxSizeMb);
          setSizeError(
            rejected.length > 0
              ? `${rejected.map((f) => f.name).join(", ")} exceed${rejected.length === 1 ? "s" : ""} the ${maxSizeMb} MB limit`
              : null
          );
          if (accepted.length === 0) return;
          field.onChange(multiple ? [...files, ...accepted] : [accepted[0]]);
        };
        return (
          <div>
            <div
              onDragOver={(e) => {
                e.preventDefault();
                setDragOver(true);
              }}
              onDragLeave={() => setDragOver(false)}
              onDrop={(e) => {
                e.preventDefault();
                setDragOver(false);
                handleFiles(e.dataTransfer.files);
              }}
              onClick={() => inputRef.current?.click()}
              className={`flex cursor-pointer flex-col items-center gap-2 rounded-lg border-2 border-dashed p-6 transition-colors ${dragOver ? "border-primary bg-primary/5" : "border-gray-300 hover:border-gray-400"}`}
            >
              <UploadIcon className="h-8 w-8 text-gray-400" />
              <span className="text-sm text-gray-500">
                Drag {multiple ? "files" : "a file"} here or click to browse
              </span>
              {(accept || maxSizeMb) && (
                <span className="text-xs text-gray-400">
                  {accept && <>Accepted: {accept}</>}
                  {accept && maxSizeMb ? " · " : ""}
                  {maxSizeMb ? `Max ${maxSizeMb} MB` : ""}
                </span>
              )}
            </div>
            <input
              ref={inputRef}
              type="file"
              accept={accept}
              multiple={multiple}
              className="hidden"
              onChange={(e) => e.target.files && handleFiles(e.target.files)}
            />
            {sizeError && <p className="mt-1 text-xs text-red-500">{sizeError}</p>}
            {files.length > 0 && (
              <div className="mt-2 flex flex-col gap-1">
                {files.map((f: File, i: number) => (
                  <div
                    key={i}
                    className="bg-muted flex items-center justify-between gap-2 rounded px-2 py-1 text-xs"
                  >
                    <div className="flex items-center gap-2">
                      <FilePreviewThumb file={f} />
                      <span>{f.name}</span>
                    </div>
                    <button
                      type="button"
                      onClick={() => field.onChange(files.filter((_: File, j: number) => j !== i))}
                      className="text-red-400 hover:text-red-600"
                    >
                      <XIcon className="h-3 w-3" />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        );
      }}
    />
  );
}

// ---------------------------------------------------------------------------
// Signature pad
// ---------------------------------------------------------------------------

function SignatureWidget({ name, control }: FieldWidgetProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [drawing, setDrawing] = useState(false);

  return (
    <Controller
      name={name}
      control={control}
      render={({ field }) => {
        const getCanvasPos = (e: React.PointerEvent<HTMLCanvasElement>) => {
          const canvas = canvasRef.current!;
          const rect = canvas.getBoundingClientRect();
          const scaleX = canvas.width / rect.width;
          const scaleY = canvas.height / rect.height;
          return {
            x: (e.clientX - rect.left) * scaleX,
            y: (e.clientY - rect.top) * scaleY,
          };
        };
        const startDraw = (e: React.PointerEvent<HTMLCanvasElement>) => {
          setDrawing(true);
          e.currentTarget.setPointerCapture(e.pointerId);
          const ctx = canvasRef.current?.getContext("2d");
          if (ctx) {
            const pos = getCanvasPos(e);
            ctx.beginPath();
            ctx.moveTo(pos.x, pos.y);
          }
        };
        const draw = (e: React.PointerEvent<HTMLCanvasElement>) => {
          if (!drawing) return;
          const ctx = canvasRef.current?.getContext("2d");
          if (ctx) {
            const pos = getCanvasPos(e);
            ctx.lineWidth = 2;
            ctx.strokeStyle = "#000";
            ctx.lineTo(pos.x, pos.y);
            ctx.stroke();
          }
        };
        const endDraw = () => {
          setDrawing(false);
          if (canvasRef.current) field.onChange(canvasRef.current.toDataURL());
        };
        const clear = () => {
          const ctx = canvasRef.current?.getContext("2d");
          if (ctx && canvasRef.current) {
            ctx.clearRect(0, 0, canvasRef.current.width, canvasRef.current.height);
            field.onChange("");
          }
        };
        return (
          <div className="flex flex-col gap-1">
            <canvas
              ref={canvasRef}
              width={400}
              height={150}
              onPointerDown={startDraw}
              onPointerMove={draw}
              onPointerUp={endDraw}
              onPointerLeave={endDraw}
              className="cursor-crosshair touch-none rounded-md border bg-white"
            />
            <button
              type="button"
              onClick={clear}
              className="self-start text-xs text-gray-500 hover:text-gray-700"
            >
              Clear signature
            </button>
          </div>
        );
      }}
    />
  );
}

// ---------------------------------------------------------------------------
// PIN input
// ---------------------------------------------------------------------------

function PinWidget({ name, register }: FieldWidgetProps) {
  return (
    <Input
      {...register(name)}
      type="password"
      inputMode="numeric"
      pattern="[0-9]*"
      maxLength={6}
      placeholder="Enter PIN"
      className="w-32 text-center tracking-[0.5em]"
    />
  );
}

// ---------------------------------------------------------------------------
// Percentage split
// ---------------------------------------------------------------------------

/**
 * Sum the numeric values of a percentage-split record. Exported for tests.
 */
export function sumSplit(value: Record<string, unknown> | undefined): number {
  if (!value) return 0;
  return Object.values(value).reduce<number>((acc, v) => {
    const n = Number(v);
    return acc + (isNaN(n) ? 0 : n);
  }, 0);
}

function PercentageSplitWidget({ name, schema, control }: FieldWidgetProps) {
  const categories = (schema["x-categories"] as string[]) || [];
  return (
    <Controller
      name={name}
      control={control}
      defaultValue={{}}
      render={({ field }) => {
        const value: Record<string, number | ""> = field.value || {};
        const total = sumSplit(value);
        const balanced = total === 100;
        const setCategory = (cat: string, raw: string) => {
          const n = raw === "" ? "" : Number(raw);
          field.onChange({ ...value, [cat]: n });
        };
        if (categories.length === 0) {
          return (
            <span className="text-muted-foreground text-xs">
              No categories defined for this split
            </span>
          );
        }
        return (
          <div className="flex flex-col gap-2 rounded-md border p-3">
            {categories.map((cat) => {
              const raw = value[cat];
              const n = typeof raw === "number" && !isNaN(raw) ? raw : 0;
              return (
                <div key={cat} className="flex items-center gap-2">
                  <span className="w-32 truncate text-sm" title={cat}>
                    {cat}
                  </span>
                  <input
                    type="range"
                    min={0}
                    max={100}
                    value={n}
                    onChange={(e) => setCategory(cat, e.target.value)}
                    className="flex-1"
                  />
                  <Input
                    type="number"
                    min={0}
                    max={100}
                    value={raw ?? ""}
                    onChange={(e) => setCategory(cat, e.target.value)}
                    className="w-20 text-right text-xs"
                  />
                  <span className="text-muted-foreground text-xs">%</span>
                </div>
              );
            })}
            <div
              className={`text-right text-xs font-medium ${balanced ? "text-green-600" : "text-red-500"}`}
            >
              Total: {total}% {balanced ? "✓" : "(must equal 100%)"}
            </div>
          </div>
        );
      }}
    />
  );
}

// ---------------------------------------------------------------------------
// Repeatable section
// ---------------------------------------------------------------------------

function RepeatableWidget({ name, schema, control }: FieldWidgetProps) {
  const items = (schema.items as Record<string, unknown>) || {};
  const innerProps = (items.properties ?? {}) as Record<string, Record<string, unknown>>;
  const innerNames = Object.keys(innerProps);

  return (
    <Controller
      name={name}
      control={control}
      defaultValue={[]}
      render={({ field }) => {
        const rows: Record<string, unknown>[] = field.value || [];
        const addRow = () => field.onChange([...rows, {}]);
        const removeRow = (i: number) => field.onChange(rows.filter((_, j) => j !== i));
        const setCell = (i: number, key: string, cellValue: unknown) => {
          const next = rows.map((row, j) => (j === i ? { ...row, [key]: cellValue } : row));
          field.onChange(next);
        };
        if (innerNames.length === 0) {
          return (
            <span className="text-muted-foreground text-xs">
              No row fields defined for this section
            </span>
          );
        }
        return (
          <div className="flex flex-col gap-2 rounded-md border p-3">
            {rows.map((row, i) => (
              <div key={i} className="flex items-end gap-2">
                {innerNames.map((innerName) => {
                  const innerSchema = innerProps[innerName];
                  const innerTitle = (innerSchema.title as string) || innerName;
                  const innerType = innerSchema.type as string;
                  const raw = row[innerName];
                  if (innerType === "boolean") {
                    return (
                      <label
                        key={innerName}
                        className="flex flex-col items-start gap-1 pb-2 text-xs"
                      >
                        <span className="text-muted-foreground">{innerTitle}</span>
                        <input
                          type="checkbox"
                          checked={Boolean(raw)}
                          onChange={(e) => setCell(i, innerName, e.target.checked)}
                          className="h-4 w-4 rounded"
                        />
                      </label>
                    );
                  }
                  const inputType =
                    innerSchema.format === "date"
                      ? "date"
                      : innerType === "number" || innerType === "integer"
                        ? "number"
                        : "text";
                  return (
                    <div key={innerName} className="flex flex-1 flex-col gap-1">
                      <span className="text-muted-foreground text-xs">{innerTitle}</span>
                      <Input
                        type={inputType}
                        value={(raw as string | number | undefined) ?? ""}
                        onChange={(e) =>
                          setCell(
                            i,
                            innerName,
                            inputType === "number"
                              ? e.target.value === ""
                                ? ""
                                : Number(e.target.value)
                              : e.target.value
                          )
                        }
                        className="text-xs"
                      />
                    </div>
                  );
                })}
                <button
                  type="button"
                  onClick={() => removeRow(i)}
                  className="pb-2 text-red-400 hover:text-red-600"
                  aria-label={`Remove row ${i + 1}`}
                >
                  <XIcon className="h-4 w-4" />
                </button>
              </div>
            ))}
            <button
              type="button"
              onClick={addRow}
              className="self-start text-xs text-blue-500 hover:text-blue-700"
            >
              + Add row
            </button>
          </div>
        );
      }}
    />
  );
}

// ---------------------------------------------------------------------------
// Static content blocks (not inputs)
// ---------------------------------------------------------------------------

function TextBlockWidget({ schema }: FieldWidgetProps) {
  const content = (schema.description as string) || (schema.title as string) || "";
  return (
    <div className="text-muted-foreground bg-muted/50 rounded-md p-4 text-sm">
      {content.split("\n").map((line, i) => (
        <p key={i}>{line}</p>
      ))}
    </div>
  );
}

function SectionHeaderWidget({ schema }: FieldWidgetProps) {
  return (
    <div className="pt-2">
      <h3 className="text-base font-semibold">{(schema.title as string) || "Section"}</h3>
      {schema.description ? (
        <p className="text-muted-foreground mt-1 text-sm">{schema.description as string}</p>
      ) : null}
      <Separator className="mt-2" />
    </div>
  );
}

function PageBreakWidget({ schema }: FieldWidgetProps) {
  return (
    <div className="flex items-center gap-3 py-2">
      <Separator className="flex-1" />
      <span className="text-muted-foreground text-xs font-medium uppercase">
        {(schema.title as string) || "Next Page"}
      </span>
      <Separator className="flex-1" />
    </div>
  );
}

function ImageWidget({ schema }: FieldWidgetProps) {
  const src = (schema["x-src"] as string) || (schema.default as string) || "";
  const alt = (schema.title as string) || "Image";
  if (!src)
    return (
      <div className="text-muted-foreground rounded border border-dashed p-4 text-center text-xs">
        Image URL not set
      </div>
    );
  return <img src={src} alt={alt} className="max-h-64 rounded-md" />;
}

function EmbedWidget({ schema }: FieldWidgetProps) {
  const src = (schema["x-src"] as string) || "";
  if (!src)
    return (
      <div className="text-muted-foreground rounded border border-dashed p-4 text-center text-xs">
        Embed URL not set
      </div>
    );
  return (
    <iframe
      src={src}
      title={(schema.title as string) || "Embedded content"}
      className="h-96 w-full rounded-md border"
      sandbox="allow-scripts allow-same-origin"
    />
  );
}

function FallbackWidget({ name, schema, register }: FieldWidgetProps) {
  return <Input {...register(name)} placeholder={`Enter ${(schema.title as string) || name}`} />;
}

// ---------------------------------------------------------------------------
// Widget resolver
// ---------------------------------------------------------------------------

function resolveWidget(schema: Record<string, unknown>): React.FC<FieldWidgetProps> {
  const xWidget = schema["x-widget"] as string | undefined;
  const type = schema.type as string;
  const format = schema.format as string | undefined;

  // x-widget overrides
  if (xWidget === "textarea") return TextareaWidget;
  if (xWidget === "rating") return RatingWidget;
  if (xWidget === "scale") return ScaleWidget;
  if (xWidget === "radio") return RadioWidget;
  if (xWidget === "file") return FileWidget;
  if (xWidget === "signature") return SignatureWidget;
  if (xWidget === "pin") return PinWidget;
  if (xWidget === "time") return DateWidget;
  if (xWidget === "text_block") return TextBlockWidget;
  if (xWidget === "section_header") return SectionHeaderWidget;
  if (xWidget === "page_break") return PageBreakWidget;
  if (xWidget === "image") return ImageWidget;
  if (xWidget === "embed") return EmbedWidget;
  if (xWidget === "percentage_split") return PercentageSplitWidget;
  if (xWidget === "repeatable") return RepeatableWidget;

  // Format-based
  if (format === "email") return EmailWidget;
  if (format === "uri" && xWidget !== "file") return UrlWidget;
  if (format === "date" || format === "date-time" || format === "time") return DateWidget;

  // Type-based
  if (type === "string" && schema.enum) return SelectWidget;
  if (type === "array") return MultiSelectWidget;
  if (type === "string") return TextWidget;
  if (type === "number" || type === "integer") return NumberWidget;
  if (type === "boolean") return BooleanWidget;

  return FallbackWidget;
}

// ---------------------------------------------------------------------------
// DynamicField — the exported component
// ---------------------------------------------------------------------------

const NON_INPUT_WIDGETS = new Set(["text_block", "section_header", "page_break", "image", "embed"]);

/**
 * Grid column classes for the x-width layout option (6-column grid).
 * Exported for use by form renderers.
 */
export function fieldWidthClass(schema: Record<string, unknown>): string {
  switch (schema["x-width"]) {
    case "half":
      return "col-span-6 md:col-span-3";
    case "third":
      return "col-span-6 md:col-span-2";
    default:
      return "col-span-6";
  }
}

export function DynamicField(props: FieldWidgetProps) {
  const { name, schema, errors } = props;
  const xWidget = schema["x-widget"] as string | undefined;
  const Widget = resolveWidget(schema);
  const error = errors[name];
  const isDisplay = NON_INPUT_WIDGETS.has(xWidget || "");
  const title =
    (schema.title as string) || name.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());

  if (isDisplay) {
    // eslint-disable-next-line react-hooks/static-components -- resolveWidget returns statically-defined module-level components, never new ones
    return <Widget {...props} />;
  }

  return (
    <div className="flex flex-col gap-1.5">
      <Label htmlFor={name}>{title}</Label>
      {/* eslint-disable-next-line react-hooks/static-components -- resolveWidget returns statically-defined module-level components, never new ones */}
      <Widget {...props} />
      {error && <p className="text-sm text-red-500">{error.message as string}</p>}
      {schema.description && !isDisplay ? (
        <p className="text-muted-foreground text-xs">{schema.description as string}</p>
      ) : null}
    </div>
  );
}
