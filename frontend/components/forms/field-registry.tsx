"use client";

import { useCallback, useRef, useState } from "react";
import type { FieldValues, UseFormRegister, FieldErrors, Control } from "react-hook-form";
import { Controller } from "react-hook-form";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
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

function BooleanWidget({ name, schema, register }: FieldWidgetProps) {
  return (
    <label className="flex items-center gap-2">
      <input type="checkbox" {...register(name)} className="h-4 w-4 rounded border" />
      <span className="text-sm">{(schema.title as string) || name}</span>
    </label>
  );
}

function EmailWidget({ name, schema, register }: FieldWidgetProps) {
  return <Input {...register(name)} type="email" placeholder={(schema.placeholder as string) || "Enter email"} />;
}

function UrlWidget({ name, schema, register }: FieldWidgetProps) {
  return <Input {...register(name)} type="url" placeholder={(schema.placeholder as string) || "Enter URL"} />;
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
              <SelectItem key={opt} value={opt}>{opt}</SelectItem>
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
            <label key={opt} className="flex items-center gap-2 cursor-pointer">
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
              <label key={opt} className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={selected.includes(opt)}
                  onChange={() => toggle(opt)}
                  className="h-4 w-4 rounded"
                />
                <span className="text-sm">{opt}</span>
              </label>
            ))}
            {options.length === 0 && <span className="text-muted-foreground text-xs">No options defined</span>}
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
            <span className="font-medium text-foreground">{field.value ?? min}</span>
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

function FileWidget({ name, schema, control }: FieldWidgetProps) {
  const [dragOver, setDragOver] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const accept = (schema["x-accept"] as string) || "";

  return (
    <Controller
      name={name}
      control={control}
      render={({ field }) => {
        const files: File[] = field.value || [];
        const handleFiles = (fileList: FileList) => {
          field.onChange([...files, ...Array.from(fileList)]);
        };
        return (
          <div>
            <div
              onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
              onDragLeave={() => setDragOver(false)}
              onDrop={(e) => { e.preventDefault(); setDragOver(false); handleFiles(e.dataTransfer.files); }}
              onClick={() => inputRef.current?.click()}
              className={`flex cursor-pointer flex-col items-center gap-2 rounded-lg border-2 border-dashed p-6 transition-colors ${dragOver ? "border-primary bg-primary/5" : "border-gray-300 hover:border-gray-400"}`}
            >
              <UploadIcon className="h-8 w-8 text-gray-400" />
              <span className="text-sm text-gray-500">Drag files here or click to browse</span>
              {accept && <span className="text-xs text-gray-400">Accepted: {accept}</span>}
            </div>
            <input ref={inputRef} type="file" accept={accept} multiple className="hidden" onChange={(e) => e.target.files && handleFiles(e.target.files)} />
            {files.length > 0 && (
              <div className="mt-2 flex flex-col gap-1">
                {files.map((f: File, i: number) => (
                  <div key={i} className="flex items-center justify-between rounded bg-muted px-2 py-1 text-xs">
                    <span>{f.name}</span>
                    <button type="button" onClick={() => field.onChange(files.filter((_: File, j: number) => j !== i))} className="text-red-400 hover:text-red-600">
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
        const getCanvasPos = (e: React.MouseEvent<HTMLCanvasElement>) => {
          const canvas = canvasRef.current!;
          const rect = canvas.getBoundingClientRect();
          const scaleX = canvas.width / rect.width;
          const scaleY = canvas.height / rect.height;
          return {
            x: (e.clientX - rect.left) * scaleX,
            y: (e.clientY - rect.top) * scaleY,
          };
        };
        const startDraw = (e: React.MouseEvent<HTMLCanvasElement>) => {
          setDrawing(true);
          const ctx = canvasRef.current?.getContext("2d");
          if (ctx) {
            const pos = getCanvasPos(e);
            ctx.beginPath();
            ctx.moveTo(pos.x, pos.y);
          }
        };
        const draw = (e: React.MouseEvent<HTMLCanvasElement>) => {
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
              onMouseDown={startDraw}
              onMouseMove={draw}
              onMouseUp={endDraw}
              onMouseLeave={endDraw}
              className="cursor-crosshair rounded-md border bg-white"
            />
            <button type="button" onClick={clear} className="self-start text-xs text-gray-500 hover:text-gray-700">
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
// Static content blocks (not inputs)
// ---------------------------------------------------------------------------

function TextBlockWidget({ schema }: FieldWidgetProps) {
  const content = (schema.description as string) || (schema.title as string) || "";
  return (
    <div className="text-muted-foreground rounded-md bg-muted/50 p-4 text-sm">
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
      {schema.description && <p className="text-muted-foreground mt-1 text-sm">{schema.description as string}</p>}
      <Separator className="mt-2" />
    </div>
  );
}

function PageBreakWidget({ schema }: FieldWidgetProps) {
  return (
    <div className="flex items-center gap-3 py-2">
      <Separator className="flex-1" />
      <span className="text-xs font-medium text-muted-foreground uppercase">{(schema.title as string) || "Next Page"}</span>
      <Separator className="flex-1" />
    </div>
  );
}

function ImageWidget({ schema }: FieldWidgetProps) {
  const src = (schema["x-src"] as string) || (schema.default as string) || "";
  const alt = (schema.title as string) || "Image";
  if (!src) return <div className="text-muted-foreground rounded border border-dashed p-4 text-center text-xs">Image URL not set</div>;
  return <img src={src} alt={alt} className="max-h-64 rounded-md" />;
}

function FallbackWidget({ name, schema, register }: FieldWidgetProps) {
  return (
    <Input {...register(name)} placeholder={`Enter ${(schema.title as string) || name}`} />
  );
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

const NON_INPUT_WIDGETS = new Set(["text_block", "section_header", "page_break", "image"]);

export function DynamicField(props: FieldWidgetProps) {
  const { name, schema, errors } = props;
  const xWidget = schema["x-widget"] as string | undefined;
  const Widget = resolveWidget(schema);
  const error = errors[name];
  const isDisplay = NON_INPUT_WIDGETS.has(xWidget || "");
  const title = (schema.title as string) || name.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());

  if (isDisplay) {
    return <Widget {...props} />;
  }

  return (
    <div className="flex flex-col gap-1.5">
      <Label htmlFor={name}>{title}</Label>
      <Widget {...props} />
      {error && <p className="text-sm text-red-500">{error.message as string}</p>}
      {schema.description && !isDisplay && (
        <p className="text-muted-foreground text-xs">{schema.description as string}</p>
      )}
    </div>
  );
}
