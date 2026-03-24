"use client";

import React, { useState } from "react";
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  type DragEndEvent,
} from "@dnd-kit/core";
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  useSortable,
  verticalListSortingStrategy,
} from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import {
  GripVerticalIcon,
  PlusIcon,
  SaveIcon,
  TrashIcon,
  SettingsIcon,
  CopyIcon,
  ChevronDownIcon,
  ChevronUpIcon,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";

const FIELD_TYPES = [
  { value: "text", label: "Text", icon: "Aa", hint: "Single-line text input" },
  { value: "textarea", label: "Textarea", icon: "¶", hint: "Multi-line text area" },
  { value: "number", label: "Number", icon: "#", hint: "Decimal number input" },
  { value: "integer", label: "Integer", icon: "1", hint: "Whole number input" },
  { value: "boolean", label: "Checkbox", icon: "☑", hint: "True/false toggle" },
  { value: "date", label: "Date", icon: "📅", hint: "Date picker (YYYY-MM-DD)" },
  { value: "datetime", label: "Date & Time", icon: "🕐", hint: "Date and time picker" },
  { value: "email", label: "Email", icon: "@", hint: "Email address with validation" },
  { value: "url", label: "URL", icon: "🔗", hint: "Web URL with validation" },
  { value: "select", label: "Dropdown", icon: "▼", hint: "Choose one from a list of options" },
  { value: "multi_select", label: "Multi-Select", icon: "☰", hint: "Choose multiple from a list" },
  { value: "rating", label: "Rating (Stars)", icon: "★", hint: "Star rating (1-5 by default)" },
  { value: "scale", label: "Scale (Slider)", icon: "─●─", hint: "Numeric slider (0-10 by default)" },
  { value: "radio", label: "Radio Buttons", icon: "◉", hint: "Choose one, displayed as radio group" },
  { value: "file", label: "File Upload", icon: "📎", hint: "Drag-and-drop file upload" },
  { value: "signature", label: "Signature", icon: "✍", hint: "Draw a signature on a canvas" },
  { value: "pin", label: "PIN Input", icon: "🔑", hint: "Masked numeric PIN entry" },
  { value: "text_block", label: "Text Block", icon: "📝", hint: "Static text, instructions, or intro paragraph" },
  { value: "section_header", label: "Section Header", icon: "═", hint: "Section title with separator" },
  { value: "page_break", label: "Page Break", icon: "⏎", hint: "Start a new page in multi-step forms" },
  { value: "image", label: "Image", icon: "🖼", hint: "Display an image from URL" },
  { value: "time", label: "Time Only", icon: "⏰", hint: "Time picker (HH:MM)" },
  { value: "repeatable", label: "Repeatable Section", icon: "⟳", hint: "Add multiple rows of the same fields" },
  { value: "percentage_split", label: "Percentage Split", icon: "%", hint: "Allocate percentages across categories" },
];

type FieldDef = {
  id: string;
  name: string;
  type: string;
  title: string;
  required: boolean;
  description: string;
  placeholder: string;
  defaultValue: string;
  width: "full" | "half" | "third";
  // Type-specific
  options: string[];
  min: string;
  max: string;
  step: string;
  prefix: string;
  suffix: string;
  minLength: string;
  maxLength: string;
  pattern: string;
  acceptedFileTypes: string;
  maxFileSize: string;
  allowMultiple: boolean;
  scaleMinLabel: string;
  scaleMaxLabel: string;
  categories: string[];
};

function defaultField(index: number): FieldDef {
  return {
    id: `field-${Date.now()}-${index}`,
    name: `field_${index + 1}`,
    type: "text",
    title: `Field ${index + 1}`,
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
  };
}

type FormBuilderProps = {
  schema: Record<string, unknown>;
  onSave: (schema: Record<string, unknown>) => void;
  onChange?: (schema: Record<string, unknown>) => void;
};

// ---------------------------------------------------------------------------
// Per-type configuration panels
// ---------------------------------------------------------------------------

function TextConfig({ field, onUpdate }: { field: FieldDef; onUpdate: (f: FieldDef) => void }) {
  return (
    <div className="grid grid-cols-3 gap-2">
      <div>
        <Label className="text-xs">Placeholder</Label>
        <Input value={field.placeholder} onChange={(e) => onUpdate({ ...field, placeholder: e.target.value })} className="text-xs" />
      </div>
      <div>
        <Label className="text-xs">Min length</Label>
        <Input value={field.minLength} onChange={(e) => onUpdate({ ...field, minLength: e.target.value })} type="number" className="text-xs" />
      </div>
      <div>
        <Label className="text-xs">Max length</Label>
        <Input value={field.maxLength} onChange={(e) => onUpdate({ ...field, maxLength: e.target.value })} type="number" className="text-xs" />
      </div>
      <div className="col-span-2">
        <Label className="text-xs">Regex pattern</Label>
        <Input value={field.pattern} onChange={(e) => onUpdate({ ...field, pattern: e.target.value })} placeholder="e.g. ^[A-Z].*" className="text-xs" />
      </div>
      <div>
        <Label className="text-xs">Default value</Label>
        <Input value={field.defaultValue} onChange={(e) => onUpdate({ ...field, defaultValue: e.target.value })} className="text-xs" />
      </div>
    </div>
  );
}

function NumberConfig({ field, onUpdate }: { field: FieldDef; onUpdate: (f: FieldDef) => void }) {
  return (
    <div className="grid grid-cols-3 gap-2">
      <div>
        <Label className="text-xs">Min</Label>
        <Input value={field.min} onChange={(e) => onUpdate({ ...field, min: e.target.value })} type="number" className="text-xs" />
      </div>
      <div>
        <Label className="text-xs">Max</Label>
        <Input value={field.max} onChange={(e) => onUpdate({ ...field, max: e.target.value })} type="number" className="text-xs" />
      </div>
      <div>
        <Label className="text-xs">Step</Label>
        <Input value={field.step} onChange={(e) => onUpdate({ ...field, step: e.target.value })} type="number" className="text-xs" />
      </div>
      <div>
        <Label className="text-xs">Prefix</Label>
        <Input value={field.prefix} onChange={(e) => onUpdate({ ...field, prefix: e.target.value })} placeholder="$" className="text-xs" />
      </div>
      <div>
        <Label className="text-xs">Suffix</Label>
        <Input value={field.suffix} onChange={(e) => onUpdate({ ...field, suffix: e.target.value })} placeholder="%" className="text-xs" />
      </div>
      <div>
        <Label className="text-xs">Default</Label>
        <Input value={field.defaultValue} onChange={(e) => onUpdate({ ...field, defaultValue: e.target.value })} type="number" className="text-xs" />
      </div>
    </div>
  );
}

function SelectConfig({ field, onUpdate }: { field: FieldDef; onUpdate: (f: FieldDef) => void }) {
  const addOption = () => onUpdate({ ...field, options: [...field.options, `Option ${field.options.length + 1}`] });
  const removeOption = (i: number) => onUpdate({ ...field, options: field.options.filter((_, j) => j !== i) });
  const updateOption = (i: number, val: string) => {
    const opts = [...field.options];
    opts[i] = val;
    onUpdate({ ...field, options: opts });
  };

  return (
    <div className="flex flex-col gap-2">
      <Label className="text-xs">Options</Label>
      {field.options.map((opt, i) => (
        <div key={i} className="flex gap-1">
          <Input value={opt} onChange={(e) => updateOption(i, e.target.value)} className="text-xs" />
          <button type="button" onClick={() => removeOption(i)} className="text-red-400 hover:text-red-600 px-1">
            <TrashIcon className="h-3 w-3" />
          </button>
        </div>
      ))}
      <button type="button" onClick={addOption} className="text-xs text-blue-500 hover:text-blue-700 self-start">
        + Add option
      </button>
    </div>
  );
}

function RatingConfig({ field, onUpdate }: { field: FieldDef; onUpdate: (f: FieldDef) => void }) {
  return (
    <div className="grid grid-cols-2 gap-2">
      <div>
        <Label className="text-xs">Max stars</Label>
        <Input value={field.max || "5"} onChange={(e) => onUpdate({ ...field, max: e.target.value })} type="number" className="text-xs" />
      </div>
      <div>
        <Label className="text-xs">Default</Label>
        <Input value={field.defaultValue} onChange={(e) => onUpdate({ ...field, defaultValue: e.target.value })} type="number" className="text-xs" />
      </div>
    </div>
  );
}

function ScaleConfig({ field, onUpdate }: { field: FieldDef; onUpdate: (f: FieldDef) => void }) {
  return (
    <div className="grid grid-cols-2 gap-2">
      <div>
        <Label className="text-xs">Min</Label>
        <Input value={field.min || "0"} onChange={(e) => onUpdate({ ...field, min: e.target.value })} type="number" className="text-xs" />
      </div>
      <div>
        <Label className="text-xs">Max</Label>
        <Input value={field.max || "10"} onChange={(e) => onUpdate({ ...field, max: e.target.value })} type="number" className="text-xs" />
      </div>
      <div>
        <Label className="text-xs">Min label</Label>
        <Input value={field.scaleMinLabel} onChange={(e) => onUpdate({ ...field, scaleMinLabel: e.target.value })} placeholder="Not at all" className="text-xs" />
      </div>
      <div>
        <Label className="text-xs">Max label</Label>
        <Input value={field.scaleMaxLabel} onChange={(e) => onUpdate({ ...field, scaleMaxLabel: e.target.value })} placeholder="Extremely" className="text-xs" />
      </div>
    </div>
  );
}

function FileConfig({ field, onUpdate }: { field: FieldDef; onUpdate: (f: FieldDef) => void }) {
  return (
    <div className="grid grid-cols-2 gap-2">
      <div>
        <Label className="text-xs">Accepted types</Label>
        <Input value={field.acceptedFileTypes} onChange={(e) => onUpdate({ ...field, acceptedFileTypes: e.target.value })} placeholder=".pdf,.jpg,.png" className="text-xs" />
      </div>
      <div>
        <Label className="text-xs">Max size (MB)</Label>
        <Input value={field.maxFileSize} onChange={(e) => onUpdate({ ...field, maxFileSize: e.target.value })} type="number" className="text-xs" />
      </div>
      <label className="flex items-center gap-1 text-xs col-span-2">
        <input type="checkbox" checked={field.allowMultiple} onChange={(e) => onUpdate({ ...field, allowMultiple: e.target.checked })} className="h-3 w-3" />
        Allow multiple files
      </label>
    </div>
  );
}

function PercentageSplitConfig({ field, onUpdate }: { field: FieldDef; onUpdate: (f: FieldDef) => void }) {
  const addCategory = () => onUpdate({ ...field, categories: [...field.categories, `Category ${field.categories.length + 1}`] });
  const removeCategory = (i: number) => onUpdate({ ...field, categories: field.categories.filter((_, j) => j !== i) });
  const updateCategory = (i: number, val: string) => {
    const cats = [...field.categories];
    cats[i] = val;
    onUpdate({ ...field, categories: cats });
  };

  return (
    <div className="flex flex-col gap-2">
      <Label className="text-xs">Categories (must sum to 100%)</Label>
      {field.categories.map((cat, i) => (
        <div key={i} className="flex gap-1">
          <Input value={cat} onChange={(e) => updateCategory(i, e.target.value)} className="text-xs" />
          <button type="button" onClick={() => removeCategory(i)} className="text-red-400 hover:text-red-600 px-1">
            <TrashIcon className="h-3 w-3" />
          </button>
        </div>
      ))}
      <button type="button" onClick={addCategory} className="text-xs text-blue-500 hover:text-blue-700 self-start">
        + Add category
      </button>
    </div>
  );
}

function TypeConfig({ field, onUpdate }: { field: FieldDef; onUpdate: (f: FieldDef) => void }) {
  switch (field.type) {
    case "text":
    case "textarea":
    case "email":
    case "url":
      return <TextConfig field={field} onUpdate={onUpdate} />;
    case "number":
    case "integer":
      return <NumberConfig field={field} onUpdate={onUpdate} />;
    case "select":
    case "multi_select":
      return <SelectConfig field={field} onUpdate={onUpdate} />;
    case "rating":
      return <RatingConfig field={field} onUpdate={onUpdate} />;
    case "scale":
      return <ScaleConfig field={field} onUpdate={onUpdate} />;
    case "file":
      return <FileConfig field={field} onUpdate={onUpdate} />;
    case "percentage_split":
      return <PercentageSplitConfig field={field} onUpdate={onUpdate} />;
    default:
      return null;
  }
}

// ---------------------------------------------------------------------------
// Sortable field row
// ---------------------------------------------------------------------------

function SortableField({
  field,
  onUpdate,
  onRemove,
  onDuplicate,
}: {
  field: FieldDef;
  onUpdate: (field: FieldDef) => void;
  onRemove: () => void;
  onDuplicate: () => void;
}) {
  const [expanded, setExpanded] = useState(false);
  const { attributes, listeners, setNodeRef, transform, transition } = useSortable({ id: field.id });
  const typeInfo = FIELD_TYPES.find((t) => t.value === field.type);

  const style = { transform: CSS.Transform.toString(transform), transition };

  return (
    <div ref={setNodeRef} style={style} className="rounded-lg border bg-white dark:bg-gray-900">
      <div className="flex items-center gap-2 p-3">
        <button type="button" {...attributes} {...listeners} className="cursor-grab text-gray-400 hover:text-gray-600">
          <GripVerticalIcon className="h-4 w-4" />
        </button>
        <span className="w-6 text-center text-xs text-gray-400" title={typeInfo?.hint}>{typeInfo?.icon}</span>
        <Input
          value={field.title}
          onChange={(e) => onUpdate({ ...field, title: e.target.value })}
          className="flex-1 border-none bg-transparent p-0 font-medium shadow-none focus-visible:ring-0"
          placeholder="Field label"
        />
        <Select value={field.type} onValueChange={(v) => onUpdate({ ...field, type: v })}>
          <SelectTrigger className="w-40">
            <SelectValue placeholder="Type">{typeInfo?.label ?? field.type}</SelectValue>
          </SelectTrigger>
          <SelectContent>
            {FIELD_TYPES.map((ft) => (
              <SelectItem key={ft.value} value={ft.value}>
                <div className="flex flex-col">
                  <span><span className="mr-2">{ft.icon}</span>{ft.label}</span>
                  <span className="text-[10px] text-muted-foreground">{ft.hint}</span>
                </div>
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Select value={field.width} onValueChange={(v) => onUpdate({ ...field, width: v as FieldDef["width"] })}>
          <SelectTrigger className="w-20">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="full">Full</SelectItem>
            <SelectItem value="half">Half</SelectItem>
            <SelectItem value="third">Third</SelectItem>
          </SelectContent>
        </Select>
        <label className="flex items-center gap-1 text-xs whitespace-nowrap">
          <input
            type="checkbox"
            checked={field.required}
            onChange={(e) => onUpdate({ ...field, required: e.target.checked })}
            className="h-3 w-3"
          />
          Req
        </label>
        <button type="button" onClick={() => setExpanded(!expanded)} className="text-gray-400 hover:text-gray-600">
          {expanded ? <ChevronUpIcon className="h-4 w-4" /> : <SettingsIcon className="h-4 w-4" />}
        </button>
        <button type="button" onClick={onDuplicate} className="text-gray-400 hover:text-gray-600">
          <CopyIcon className="h-4 w-4" />
        </button>
        <button type="button" onClick={onRemove} className="text-red-400 hover:text-red-600">
          <TrashIcon className="h-4 w-4" />
        </button>
      </div>

      {!expanded && typeInfo?.hint && (
        <div className="px-3 pb-2 text-[11px] text-muted-foreground">{typeInfo.hint}</div>
      )}

      {expanded && (
        <div className="border-t px-3 pb-3 pt-3">
          <div className="mb-3 grid grid-cols-3 gap-2">
            <div>
              <Label className="text-xs">Field name (slug)</Label>
              <Input
                value={field.name}
                onChange={(e) => onUpdate({ ...field, name: e.target.value.replace(/\s/g, "_").toLowerCase() })}
                className="text-xs"
              />
            </div>
            <div>
              <Label className="text-xs">Help text</Label>
              <Input value={field.description} onChange={(e) => onUpdate({ ...field, description: e.target.value })} className="text-xs" />
            </div>
            <div>
              <Label className="text-xs">Placeholder</Label>
              <Input value={field.placeholder} onChange={(e) => onUpdate({ ...field, placeholder: e.target.value })} className="text-xs" />
            </div>
          </div>
          <TypeConfig field={field} onUpdate={onUpdate} />
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Schema conversion
// ---------------------------------------------------------------------------

function schemaToFields(schema: Record<string, unknown>): FieldDef[] {
  const properties = (schema.properties || {}) as Record<string, Record<string, unknown>>;
  const required = new Set((schema.required || []) as string[]);
  return Object.entries(properties).map(([name, def], i) => ({
    ...defaultField(i),
    id: `field-${i}`,
    name,
    type: resolveType(def),
    title: (def.title as string) || name.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase()),
    required: required.has(name),
    description: (def.description as string) || "",
    placeholder: (def.placeholder as string) || "",
    options: (def.enum as string[]) || ((def.items as Record<string, unknown>)?.enum as string[]) || [],
    min: def.minimum != null ? String(def.minimum) : "",
    max: def.maximum != null ? String(def.maximum) : "",
  }));
}

function resolveType(def: Record<string, unknown>): string {
  const xWidget = def["x-widget"] as string;
  if (xWidget) return xWidget;
  const format = def.format as string;
  if (format === "email") return "email";
  if (format === "uri") return "url";
  if (format === "date") return "date";
  if (format === "date-time") return "datetime";
  const type = def.type as string;
  if (type === "integer") return "integer";
  if (type === "number") return "number";
  if (type === "boolean") return "boolean";
  if (type === "string" && def.enum) return "select";
  if (type === "array") return "multi_select";
  return "text";
}

function fieldsToSchema(fields: FieldDef[]): Record<string, unknown> {
  const properties: Record<string, Record<string, unknown>> = {};
  const required: string[] = [];

  for (const field of fields) {
    const prop: Record<string, unknown> = {};

    switch (field.type) {
      case "text": case "textarea": case "email": case "url": case "date": case "datetime": case "signature":
        prop.type = "string"; break;
      case "number": prop.type = "number"; break;
      case "integer": case "rating": case "scale": prop.type = "integer"; break;
      case "boolean": prop.type = "boolean"; break;
      case "select": prop.type = "string"; break;
      case "multi_select": case "repeatable": prop.type = "array"; break;
      case "percentage_split": prop.type = "object"; break;
      case "file": prop.type = "string"; break;
      default: prop.type = "string";
    }

    if (field.type === "email") prop.format = "email";
    if (field.type === "url") prop.format = "uri";
    if (field.type === "date") prop.format = "date";
    if (field.type === "datetime") prop.format = "date-time";
    if (field.type === "textarea") prop["x-widget"] = "textarea";
    if (field.type === "rating") { prop["x-widget"] = "rating"; prop.minimum = 1; prop.maximum = parseInt(field.max) || 5; }
    if (field.type === "scale") { prop["x-widget"] = "scale"; prop.minimum = parseInt(field.min) || 0; prop.maximum = parseInt(field.max) || 10; }
    if (field.type === "signature") prop["x-widget"] = "signature";
    if (field.type === "file") { prop.format = "uri"; prop["x-widget"] = "file"; }
    if (field.type === "percentage_split") prop["x-widget"] = "percentage_split";

    if (field.min && !["rating", "scale"].includes(field.type)) prop.minimum = parseFloat(field.min);
    if (field.max && !["rating", "scale"].includes(field.type)) prop.maximum = parseFloat(field.max);
    if (field.minLength) prop.minLength = parseInt(field.minLength);
    if (field.maxLength) prop.maxLength = parseInt(field.maxLength);
    if (field.pattern) prop.pattern = field.pattern;
    if (field.placeholder) prop.placeholder = field.placeholder;

    if (field.options.length > 0) {
      if (field.type === "select") prop.enum = field.options;
      else if (field.type === "multi_select") prop.items = { type: "string", enum: field.options };
    }

    if (field.title) prop.title = field.title;
    if (field.description) prop.description = field.description;
    if (field.defaultValue) prop.default = field.defaultValue;

    properties[field.name] = prop;
    if (field.required) required.push(field.name);
  }

  return { type: "object", properties, required };
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

export function FormBuilder({ schema, onSave, onChange }: FormBuilderProps) {
  const [fields, setFields] = useState<FieldDef[]>(() => schemaToFields(schema));
  const [allExpanded, setAllExpanded] = useState(false);

  // Live preview: notify parent on every field change
  const fieldsJson = JSON.stringify(fields);
  React.useEffect(() => {
    if (onChange) {
      onChange(fieldsToSchema(fields));
    }
  }, [fieldsJson]); // eslint-disable-line react-hooks/exhaustive-deps

  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates }),
  );

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    if (over && active.id !== over.id) {
      setFields((items) => {
        const oldIndex = items.findIndex((i) => i.id === active.id);
        const newIndex = items.findIndex((i) => i.id === over.id);
        return arrayMove(items, oldIndex, newIndex);
      });
    }
  };

  const addField = () => {
    setFields((prev) => [...prev, defaultField(prev.length)]);
  };

  const updateField = (id: string, updated: FieldDef) => {
    setFields((prev) => prev.map((f) => (f.id === id ? updated : f)));
  };

  const removeField = (id: string) => {
    setFields((prev) => prev.filter((f) => f.id !== id));
  };

  const duplicateField = (id: string) => {
    setFields((prev) => {
      const source = prev.find((f) => f.id === id);
      if (!source) return prev;
      const idx = prev.findIndex((f) => f.id === id);
      const clone = { ...source, id: `field-${Date.now()}`, name: `${source.name}_copy` };
      const next = [...prev];
      next.splice(idx + 1, 0, clone);
      return next;
    });
  };

  const handleSave = () => {
    onSave(fieldsToSchema(fields));
  };

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <div className="flex gap-2">
          <Button type="button" variant="outline" size="sm" onClick={addField}>
            <PlusIcon className="mr-1 h-3 w-3" /> Add Field
          </Button>
          <Button type="button" variant="ghost" size="sm" onClick={() => setAllExpanded(!allExpanded)}>
            {allExpanded ? <ChevronUpIcon className="mr-1 h-3 w-3" /> : <ChevronDownIcon className="mr-1 h-3 w-3" />}
            {allExpanded ? "Collapse All" : "Expand All"}
          </Button>
        </div>
        <Button type="button" size="sm" onClick={handleSave}>
          <SaveIcon className="mr-1 h-3 w-3" /> Save Schema
        </Button>
      </div>

      <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
        <SortableContext items={fields.map((f) => f.id)} strategy={verticalListSortingStrategy}>
          <div className="flex flex-col gap-2">
            {fields.map((field) => (
              <SortableField
                key={field.id}
                field={field}
                onUpdate={(updated) => updateField(field.id, updated)}
                onRemove={() => removeField(field.id)}
                onDuplicate={() => duplicateField(field.id)}
              />
            ))}
          </div>
        </SortableContext>
      </DndContext>

      {fields.length === 0 && (
        <div className="text-muted-foreground rounded-lg border border-dashed p-8 text-center">
          No fields yet. Click &quot;Add Field&quot; to start building your form.
        </div>
      )}

      <div className="text-muted-foreground text-xs">
        Drag to reorder. Click ⚙ to configure type-specific settings.
        {fields.length > 0 && (
          <span>
            {" "}{fields.length} field{fields.length !== 1 ? "s" : ""}, {fields.filter((f) => f.required).length} required.
          </span>
        )}
      </div>
    </div>
  );
}
