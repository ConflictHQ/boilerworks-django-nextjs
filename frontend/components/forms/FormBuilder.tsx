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
import type { LogicRule } from "./logic-engine";

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
  {
    value: "scale",
    label: "Scale (Slider)",
    icon: "─●─",
    hint: "Numeric slider (0-10 by default)",
  },
  {
    value: "radio",
    label: "Radio Buttons",
    icon: "◉",
    hint: "Choose one, displayed as radio group",
  },
  { value: "file", label: "File Upload", icon: "📎", hint: "Drag-and-drop file upload" },
  { value: "signature", label: "Signature", icon: "✍", hint: "Draw a signature on a canvas" },
  { value: "pin", label: "PIN Input", icon: "🔑", hint: "Masked numeric PIN entry" },
  {
    value: "text_block",
    label: "Text Block",
    icon: "📝",
    hint: "Static text, instructions, or intro paragraph",
  },
  {
    value: "section_header",
    label: "Section Header",
    icon: "═",
    hint: "Section title with separator",
  },
  {
    value: "page_break",
    label: "Page Break",
    icon: "⏎",
    hint: "Start a new page in multi-step forms",
  },
  { value: "image", label: "Image", icon: "🖼", hint: "Display an image from URL" },
  { value: "embed", label: "URL Embed", icon: "🌐", hint: "Embed content from a URL (iframe)" },
  { value: "time", label: "Time Only", icon: "⏰", hint: "Time picker (HH:MM)" },
  {
    value: "repeatable",
    label: "Repeatable Section",
    icon: "⟳",
    hint: "Add multiple rows of the same fields",
  },
  {
    value: "percentage_split",
    label: "Percentage Split",
    icon: "%",
    hint: "Allocate percentages across categories",
  },
];

export type InnerFieldDef = {
  name: string;
  title: string;
  type: "text" | "number" | "integer" | "boolean" | "date";
};

export type FieldDef = {
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
  imageSrc: string;
  innerFields: InnerFieldDef[];
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
    imageSrc: "",
    innerFields: [],
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
        <Input
          value={field.placeholder}
          onChange={(e) => onUpdate({ ...field, placeholder: e.target.value })}
          className="text-xs"
        />
      </div>
      <div>
        <Label className="text-xs">Min length</Label>
        <Input
          value={field.minLength}
          onChange={(e) => onUpdate({ ...field, minLength: e.target.value })}
          type="number"
          className="text-xs"
        />
      </div>
      <div>
        <Label className="text-xs">Max length</Label>
        <Input
          value={field.maxLength}
          onChange={(e) => onUpdate({ ...field, maxLength: e.target.value })}
          type="number"
          className="text-xs"
        />
      </div>
      <div className="col-span-2">
        <Label className="text-xs">Regex pattern</Label>
        <Input
          value={field.pattern}
          onChange={(e) => onUpdate({ ...field, pattern: e.target.value })}
          placeholder="e.g. ^[A-Z].*"
          className="text-xs"
        />
      </div>
      <div>
        <Label className="text-xs">Default value</Label>
        <Input
          value={field.defaultValue}
          onChange={(e) => onUpdate({ ...field, defaultValue: e.target.value })}
          className="text-xs"
        />
      </div>
    </div>
  );
}

function NumberConfig({ field, onUpdate }: { field: FieldDef; onUpdate: (f: FieldDef) => void }) {
  return (
    <div className="grid grid-cols-3 gap-2">
      <div>
        <Label className="text-xs">Min</Label>
        <Input
          value={field.min}
          onChange={(e) => onUpdate({ ...field, min: e.target.value })}
          type="number"
          className="text-xs"
        />
      </div>
      <div>
        <Label className="text-xs">Max</Label>
        <Input
          value={field.max}
          onChange={(e) => onUpdate({ ...field, max: e.target.value })}
          type="number"
          className="text-xs"
        />
      </div>
      <div>
        <Label className="text-xs">Step</Label>
        <Input
          value={field.step}
          onChange={(e) => onUpdate({ ...field, step: e.target.value })}
          type="number"
          className="text-xs"
        />
      </div>
      <div>
        <Label className="text-xs">Prefix</Label>
        <Input
          value={field.prefix}
          onChange={(e) => onUpdate({ ...field, prefix: e.target.value })}
          placeholder="$"
          className="text-xs"
        />
      </div>
      <div>
        <Label className="text-xs">Suffix</Label>
        <Input
          value={field.suffix}
          onChange={(e) => onUpdate({ ...field, suffix: e.target.value })}
          placeholder="%"
          className="text-xs"
        />
      </div>
      <div>
        <Label className="text-xs">Default</Label>
        <Input
          value={field.defaultValue}
          onChange={(e) => onUpdate({ ...field, defaultValue: e.target.value })}
          type="number"
          className="text-xs"
        />
      </div>
    </div>
  );
}

function SelectConfig({ field, onUpdate }: { field: FieldDef; onUpdate: (f: FieldDef) => void }) {
  const addOption = () =>
    onUpdate({ ...field, options: [...field.options, `Option ${field.options.length + 1}`] });
  const removeOption = (i: number) =>
    onUpdate({ ...field, options: field.options.filter((_, j) => j !== i) });
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
          <Input
            value={opt}
            onChange={(e) => updateOption(i, e.target.value)}
            className="text-xs"
          />
          <button
            type="button"
            onClick={() => removeOption(i)}
            className="px-1 text-red-400 hover:text-red-600"
          >
            <TrashIcon className="h-3 w-3" />
          </button>
        </div>
      ))}
      <button
        type="button"
        onClick={addOption}
        className="self-start text-xs text-blue-500 hover:text-blue-700"
      >
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
        <Input
          value={field.max || "5"}
          onChange={(e) => onUpdate({ ...field, max: e.target.value })}
          type="number"
          className="text-xs"
        />
      </div>
      <div>
        <Label className="text-xs">Default</Label>
        <Input
          value={field.defaultValue}
          onChange={(e) => onUpdate({ ...field, defaultValue: e.target.value })}
          type="number"
          className="text-xs"
        />
      </div>
    </div>
  );
}

function ScaleConfig({ field, onUpdate }: { field: FieldDef; onUpdate: (f: FieldDef) => void }) {
  return (
    <div className="grid grid-cols-2 gap-2">
      <div>
        <Label className="text-xs">Min</Label>
        <Input
          value={field.min || "0"}
          onChange={(e) => onUpdate({ ...field, min: e.target.value })}
          type="number"
          className="text-xs"
        />
      </div>
      <div>
        <Label className="text-xs">Max</Label>
        <Input
          value={field.max || "10"}
          onChange={(e) => onUpdate({ ...field, max: e.target.value })}
          type="number"
          className="text-xs"
        />
      </div>
      <div>
        <Label className="text-xs">Min label</Label>
        <Input
          value={field.scaleMinLabel}
          onChange={(e) => onUpdate({ ...field, scaleMinLabel: e.target.value })}
          placeholder="Not at all"
          className="text-xs"
        />
      </div>
      <div>
        <Label className="text-xs">Max label</Label>
        <Input
          value={field.scaleMaxLabel}
          onChange={(e) => onUpdate({ ...field, scaleMaxLabel: e.target.value })}
          placeholder="Extremely"
          className="text-xs"
        />
      </div>
    </div>
  );
}

function FileConfig({ field, onUpdate }: { field: FieldDef; onUpdate: (f: FieldDef) => void }) {
  return (
    <div className="grid grid-cols-2 gap-2">
      <div>
        <Label className="text-xs">Accepted types</Label>
        <Input
          value={field.acceptedFileTypes}
          onChange={(e) => onUpdate({ ...field, acceptedFileTypes: e.target.value })}
          placeholder=".pdf,.jpg,.png"
          className="text-xs"
        />
      </div>
      <div>
        <Label className="text-xs">Max size (MB)</Label>
        <Input
          value={field.maxFileSize}
          onChange={(e) => onUpdate({ ...field, maxFileSize: e.target.value })}
          type="number"
          className="text-xs"
        />
      </div>
      <label className="col-span-2 flex items-center gap-1 text-xs">
        <input
          type="checkbox"
          checked={field.allowMultiple}
          onChange={(e) => onUpdate({ ...field, allowMultiple: e.target.checked })}
          className="h-3 w-3"
        />
        Allow multiple files
      </label>
    </div>
  );
}

function PercentageSplitConfig({
  field,
  onUpdate,
}: {
  field: FieldDef;
  onUpdate: (f: FieldDef) => void;
}) {
  const addCategory = () =>
    onUpdate({
      ...field,
      categories: [...field.categories, `Category ${field.categories.length + 1}`],
    });
  const removeCategory = (i: number) =>
    onUpdate({ ...field, categories: field.categories.filter((_, j) => j !== i) });
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
          <Input
            value={cat}
            onChange={(e) => updateCategory(i, e.target.value)}
            className="text-xs"
          />
          <button
            type="button"
            onClick={() => removeCategory(i)}
            className="px-1 text-red-400 hover:text-red-600"
          >
            <TrashIcon className="h-3 w-3" />
          </button>
        </div>
      ))}
      <button
        type="button"
        onClick={addCategory}
        className="self-start text-xs text-blue-500 hover:text-blue-700"
      >
        + Add category
      </button>
    </div>
  );
}

function TextBlockConfig({
  field,
  onUpdate,
}: {
  field: FieldDef;
  onUpdate: (f: FieldDef) => void;
}) {
  return (
    <div className="flex flex-col gap-1">
      <Label className="text-xs">Content</Label>
      <Textarea
        value={field.description}
        onChange={(e) => onUpdate({ ...field, description: e.target.value })}
        placeholder="Static text shown to the respondent (line breaks preserved)"
        rows={4}
        className="text-xs"
      />
    </div>
  );
}

function ImageConfig({ field, onUpdate }: { field: FieldDef; onUpdate: (f: FieldDef) => void }) {
  return (
    <div className="flex flex-col gap-1">
      <Label className="text-xs">Image URL</Label>
      <Input
        value={field.imageSrc}
        onChange={(e) => onUpdate({ ...field, imageSrc: e.target.value })}
        placeholder="https://example.com/diagram.png"
        className="text-xs"
      />
    </div>
  );
}

function EmbedConfig({ field, onUpdate }: { field: FieldDef; onUpdate: (f: FieldDef) => void }) {
  return (
    <div className="flex flex-col gap-1">
      <Label className="text-xs">Embed URL</Label>
      <Input
        value={field.imageSrc}
        onChange={(e) => onUpdate({ ...field, imageSrc: e.target.value })}
        placeholder="https://example.com/page-to-embed"
        className="text-xs"
      />
    </div>
  );
}

const INNER_FIELD_TYPES: { value: InnerFieldDef["type"]; label: string }[] = [
  { value: "text", label: "Text" },
  { value: "number", label: "Number" },
  { value: "integer", label: "Integer" },
  { value: "boolean", label: "Checkbox" },
  { value: "date", label: "Date" },
];

function RepeatableConfig({
  field,
  onUpdate,
}: {
  field: FieldDef;
  onUpdate: (f: FieldDef) => void;
}) {
  const addInner = () =>
    onUpdate({
      ...field,
      innerFields: [
        ...field.innerFields,
        {
          name: `column_${field.innerFields.length + 1}`,
          title: `Column ${field.innerFields.length + 1}`,
          type: "text",
        },
      ],
    });
  const removeInner = (i: number) =>
    onUpdate({ ...field, innerFields: field.innerFields.filter((_, j) => j !== i) });
  const updateInner = (i: number, updates: Partial<InnerFieldDef>) => {
    const inner = [...field.innerFields];
    inner[i] = { ...inner[i], ...updates };
    onUpdate({ ...field, innerFields: inner });
  };

  return (
    <div className="flex flex-col gap-2">
      <Label className="text-xs">Row fields (each repeated row has these)</Label>
      {field.innerFields.map((inner, i) => (
        <div key={i} className="flex gap-1">
          <Input
            value={inner.title}
            onChange={(e) => {
              const title = e.target.value;
              updateInner(i, {
                name: title.trim().toLowerCase().replace(/\s+/g, "_") || `column_${i + 1}`,
                title,
              });
            }}
            placeholder="Label"
            className="flex-1 text-xs"
          />
          <Select
            value={inner.type}
            onValueChange={(v) => updateInner(i, { type: v as InnerFieldDef["type"] })}
          >
            <SelectTrigger className="w-28 text-xs">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {INNER_FIELD_TYPES.map((t) => (
                <SelectItem key={t.value} value={t.value}>
                  {t.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <button
            type="button"
            onClick={() => removeInner(i)}
            className="px-1 text-red-400 hover:text-red-600"
          >
            <TrashIcon className="h-3 w-3" />
          </button>
        </div>
      ))}
      <button
        type="button"
        onClick={addInner}
        className="self-start text-xs text-blue-500 hover:text-blue-700"
      >
        + Add row field
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
    case "radio":
      return <SelectConfig field={field} onUpdate={onUpdate} />;
    case "rating":
      return <RatingConfig field={field} onUpdate={onUpdate} />;
    case "scale":
      return <ScaleConfig field={field} onUpdate={onUpdate} />;
    case "file":
      return <FileConfig field={field} onUpdate={onUpdate} />;
    case "percentage_split":
      return <PercentageSplitConfig field={field} onUpdate={onUpdate} />;
    case "text_block":
      return <TextBlockConfig field={field} onUpdate={onUpdate} />;
    case "image":
      return <ImageConfig field={field} onUpdate={onUpdate} />;
    case "embed":
      return <EmbedConfig field={field} onUpdate={onUpdate} />;
    case "repeatable":
      return <RepeatableConfig field={field} onUpdate={onUpdate} />;
    default:
      return null;
  }
}

// ---------------------------------------------------------------------------
// Sortable field row
// ---------------------------------------------------------------------------

function SortableField({
  field,
  expanded,
  onToggleExpanded,
  onUpdate,
  onRemove,
  onDuplicate,
}: {
  field: FieldDef;
  expanded: boolean;
  onToggleExpanded: () => void;
  onUpdate: (field: FieldDef) => void;
  onRemove: () => void;
  onDuplicate: () => void;
}) {
  const { attributes, listeners, setNodeRef, transform, transition } = useSortable({
    id: field.id,
  });
  const typeInfo = FIELD_TYPES.find((t) => t.value === field.type);

  const style = { transform: CSS.Transform.toString(transform), transition };

  return (
    <div ref={setNodeRef} style={style} className="rounded-lg border bg-white dark:bg-gray-900">
      <div className="flex items-center gap-2 p-3">
        <button
          type="button"
          {...attributes}
          {...listeners}
          className="cursor-grab text-gray-400 hover:text-gray-600"
        >
          <GripVerticalIcon className="h-4 w-4" />
        </button>
        <span className="w-6 text-center text-xs text-gray-400" title={typeInfo?.hint}>
          {typeInfo?.icon}
        </span>
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
                  <span>
                    <span className="mr-2">{ft.icon}</span>
                    {ft.label}
                  </span>
                  <span className="text-muted-foreground text-[10px]">{ft.hint}</span>
                </div>
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Select
          value={field.width}
          onValueChange={(v) => onUpdate({ ...field, width: v as FieldDef["width"] })}
        >
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
        <button
          type="button"
          onClick={onToggleExpanded}
          className="text-gray-400 hover:text-gray-600"
        >
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
        <div className="text-muted-foreground px-3 pb-2 text-[11px]">{typeInfo.hint}</div>
      )}

      {expanded && (
        <div className="border-t px-3 pt-3 pb-3">
          <div className="mb-3 grid grid-cols-3 gap-2">
            <div>
              <Label className="text-xs">Field name (slug)</Label>
              <Input
                value={field.name}
                onChange={(e) =>
                  onUpdate({ ...field, name: e.target.value.replace(/\s/g, "_").toLowerCase() })
                }
                className="text-xs"
              />
            </div>
            <div>
              <Label className="text-xs">Help text</Label>
              <Input
                value={field.description}
                onChange={(e) => onUpdate({ ...field, description: e.target.value })}
                className="text-xs"
              />
            </div>
            <div>
              <Label className="text-xs">Placeholder</Label>
              <Input
                value={field.placeholder}
                onChange={(e) => onUpdate({ ...field, placeholder: e.target.value })}
                className="text-xs"
              />
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

export function schemaToFields(schema: Record<string, unknown>): FieldDef[] {
  const properties = (schema.properties || {}) as Record<string, Record<string, unknown>>;
  const required = new Set((schema.required || []) as string[]);
  return Object.entries(properties).map(([name, def], i) => ({
    ...defaultField(i),
    id: `field-${i}`,
    name,
    type: resolveType(def),
    title:
      (def.title as string) || name.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase()),
    required: required.has(name),
    description: (def.description as string) || "",
    placeholder: (def.placeholder as string) || "",
    defaultValue: def.default != null ? String(def.default) : "",
    width: (def["x-width"] as FieldDef["width"]) || "full",
    options:
      (def.enum as string[]) || ((def.items as Record<string, unknown>)?.enum as string[]) || [],
    min: def.minimum != null ? String(def.minimum) : "",
    max: def.maximum != null ? String(def.maximum) : "",
    step: def["x-step"] != null ? String(def["x-step"]) : "",
    prefix: (def["x-prefix"] as string) || "",
    suffix: (def["x-suffix"] as string) || "",
    minLength: def.minLength != null ? String(def.minLength) : "",
    maxLength: def.maxLength != null ? String(def.maxLength) : "",
    pattern: (def.pattern as string) || "",
    acceptedFileTypes: (def["x-accept"] as string) || "",
    maxFileSize: def["x-max-size-mb"] != null ? String(def["x-max-size-mb"]) : "",
    allowMultiple: Boolean(def["x-multiple"]),
    scaleMinLabel: (def["x-min-label"] as string) || "",
    scaleMaxLabel: (def["x-max-label"] as string) || "",
    categories: (def["x-categories"] as string[]) || [],
    imageSrc: (def["x-src"] as string) || "",
    innerFields: itemsToInnerFields(def.items as Record<string, unknown> | undefined),
  }));
}

function itemsToInnerFields(items: Record<string, unknown> | undefined): InnerFieldDef[] {
  const props = (items?.properties ?? {}) as Record<string, Record<string, unknown>>;
  return Object.entries(props).map(([name, def]) => ({
    name,
    title:
      (def.title as string) || name.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase()),
    type:
      def.format === "date"
        ? "date"
        : def.type === "number" || def.type === "integer" || def.type === "boolean"
          ? (def.type as InnerFieldDef["type"])
          : "text",
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
  if (format === "time") return "time";
  const type = def.type as string;
  if (type === "integer") return "integer";
  if (type === "number") return "number";
  if (type === "boolean") return "boolean";
  if (type === "string" && def.enum) return "select";
  if (type === "array") return "multi_select";
  return "text";
}

const NUMERIC_TYPES = new Set(["number", "integer", "rating", "scale"]);

function innerFieldsToItems(innerFields: InnerFieldDef[]): Record<string, unknown> {
  const properties: Record<string, Record<string, unknown>> = {};
  for (const inner of innerFields) {
    const prop: Record<string, unknown> = { title: inner.title };
    if (inner.type === "date") {
      prop.type = "string";
      prop.format = "date";
    } else if (inner.type === "text") {
      prop.type = "string";
    } else {
      prop.type = inner.type;
    }
    properties[inner.name] = prop;
  }
  return { type: "object", properties };
}

export function fieldsToSchema(fields: FieldDef[]): Record<string, unknown> {
  const properties: Record<string, Record<string, unknown>> = {};
  const required: string[] = [];

  for (const field of fields) {
    const prop: Record<string, unknown> = {};

    switch (field.type) {
      case "number":
        prop.type = "number";
        break;
      case "integer":
      case "rating":
      case "scale":
        prop.type = "integer";
        break;
      case "boolean":
        prop.type = "boolean";
        break;
      case "multi_select":
      case "repeatable":
        prop.type = "array";
        break;
      case "percentage_split":
        prop.type = "object";
        break;
      default:
        prop.type = "string";
    }

    if (field.type === "email") prop.format = "email";
    if (field.type === "url") prop.format = "uri";
    if (field.type === "date") prop.format = "date";
    if (field.type === "datetime") prop.format = "date-time";
    if (field.type === "time") {
      prop.format = "time";
      prop["x-widget"] = "time";
    }
    if (field.type === "textarea") prop["x-widget"] = "textarea";
    if (field.type === "radio") prop["x-widget"] = "radio";
    if (field.type === "pin") prop["x-widget"] = "pin";
    if (field.type === "rating") {
      prop["x-widget"] = "rating";
      prop.minimum = 1;
      prop.maximum = parseInt(field.max) || 5;
    }
    if (field.type === "scale") {
      prop["x-widget"] = "scale";
      prop.minimum = parseInt(field.min) || 0;
      prop.maximum = parseInt(field.max) || 10;
      if (field.scaleMinLabel) prop["x-min-label"] = field.scaleMinLabel;
      if (field.scaleMaxLabel) prop["x-max-label"] = field.scaleMaxLabel;
    }
    if (field.type === "signature") prop["x-widget"] = "signature";
    if (field.type === "file") {
      prop.format = "uri";
      prop["x-widget"] = "file";
      if (field.acceptedFileTypes) prop["x-accept"] = field.acceptedFileTypes;
      if (field.maxFileSize) prop["x-max-size-mb"] = parseFloat(field.maxFileSize);
      if (field.allowMultiple) prop["x-multiple"] = true;
    }
    if (field.type === "percentage_split") {
      prop["x-widget"] = "percentage_split";
      if (field.categories.length > 0) prop["x-categories"] = field.categories;
    }
    if (field.type === "repeatable") {
      prop["x-widget"] = "repeatable";
      prop.items = innerFieldsToItems(field.innerFields);
    }
    if (["text_block", "section_header", "page_break"].includes(field.type)) {
      prop["x-widget"] = field.type;
    }
    if (field.type === "image" || field.type === "embed") {
      prop["x-widget"] = field.type;
      if (field.imageSrc) prop["x-src"] = field.imageSrc;
    }

    if (field.min && !["rating", "scale"].includes(field.type))
      prop.minimum = parseFloat(field.min);
    if (field.max && !["rating", "scale"].includes(field.type))
      prop.maximum = parseFloat(field.max);
    if (field.step && ["number", "integer"].includes(field.type))
      prop["x-step"] = parseFloat(field.step);
    if (field.prefix && ["number", "integer"].includes(field.type)) prop["x-prefix"] = field.prefix;
    if (field.suffix && ["number", "integer"].includes(field.type)) prop["x-suffix"] = field.suffix;
    if (field.minLength) prop.minLength = parseInt(field.minLength);
    if (field.maxLength) prop.maxLength = parseInt(field.maxLength);
    if (field.pattern) prop.pattern = field.pattern;
    if (field.placeholder) prop.placeholder = field.placeholder;
    if (field.width !== "full") prop["x-width"] = field.width;

    if (field.options.length > 0) {
      if (field.type === "select" || field.type === "radio") prop.enum = field.options;
      else if (field.type === "multi_select") prop.items = { type: "string", enum: field.options };
    }

    if (field.title) prop.title = field.title;
    if (field.description) prop.description = field.description;
    if (field.defaultValue) {
      prop.default = NUMERIC_TYPES.has(field.type)
        ? parseFloat(field.defaultValue)
        : field.defaultValue;
    }

    properties[field.name] = prop;
    if (field.required) required.push(field.name);
  }

  return { type: "object", properties, required };
}

// ---------------------------------------------------------------------------
// Conditional logic editor
// ---------------------------------------------------------------------------

const LOGIC_OPS: { value: LogicRule["condition"]["op"]; label: string; needsValue: boolean }[] = [
  { value: "eq", label: "equals", needsValue: true },
  { value: "neq", label: "does not equal", needsValue: true },
  { value: "gt", label: "is greater than", needsValue: true },
  { value: "lt", label: "is less than", needsValue: true },
  { value: "contains", label: "contains", needsValue: true },
  { value: "is_empty", label: "is empty", needsValue: false },
  { value: "is_not_empty", label: "is not empty", needsValue: false },
];

const LOGIC_ACTIONS: { value: LogicRule["action"]; label: string }[] = [
  { value: "show", label: "show" },
  { value: "hide", label: "hide" },
  { value: "require", label: "require" },
];

function opNeedsValue(op: LogicRule["condition"]["op"]): boolean {
  return LOGIC_OPS.find((o) => o.value === op)?.needsValue ?? true;
}

function LogicRulesEditor({
  fields,
  rules,
  onChange,
}: {
  fields: FieldDef[];
  rules: LogicRule[];
  onChange: (rules: LogicRule[]) => void;
}) {
  const inputFields = fields.filter(
    (f) => !["text_block", "section_header", "page_break", "image", "embed"].includes(f.type)
  );

  const addRule = () => {
    const first = inputFields[0]?.name ?? "";
    onChange([
      ...rules,
      { condition: { field: first, op: "eq", value: "" }, action: "show", target: first },
    ]);
  };
  const removeRule = (i: number) => onChange(rules.filter((_, j) => j !== i));
  const updateRule = (i: number, updates: Partial<LogicRule>) => {
    onChange(rules.map((r, j) => (j === i ? { ...r, ...updates } : r)));
  };

  const fieldSelect = (value: string, onValue: (v: string) => void) => (
    <Select value={value} onValueChange={onValue}>
      <SelectTrigger className="w-40">
        <SelectValue placeholder="Field" />
      </SelectTrigger>
      <SelectContent>
        {inputFields.map((f) => (
          <SelectItem key={f.name} value={f.name}>
            {f.title || f.name}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );

  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold">Conditional Logic</h3>
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={addRule}
          disabled={inputFields.length === 0}
        >
          <PlusIcon className="mr-1 h-3 w-3" /> Add Rule
        </Button>
      </div>
      {rules.length === 0 && (
        <p className="text-muted-foreground text-xs">
          No rules. Rules run while the form is filled in, e.g. &quot;when expense_type equals
          travel, show destination&quot;.
        </p>
      )}
      {rules.map((rule, i) => (
        <div key={i} className="flex flex-wrap items-center gap-2 rounded-md border p-2 text-sm">
          <span className="text-muted-foreground text-xs">When</span>
          {fieldSelect(rule.condition.field, (v) =>
            updateRule(i, { condition: { ...rule.condition, field: v } })
          )}
          <Select
            value={rule.condition.op}
            onValueChange={(v) =>
              updateRule(i, {
                condition: { ...rule.condition, op: v as LogicRule["condition"]["op"] },
              })
            }
          >
            <SelectTrigger className="w-40">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {LOGIC_OPS.map((op) => (
                <SelectItem key={op.value} value={op.value}>
                  {op.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {opNeedsValue(rule.condition.op) && (
            <Input
              value={String(rule.condition.value ?? "")}
              onChange={(e) =>
                updateRule(i, { condition: { ...rule.condition, value: e.target.value } })
              }
              placeholder="value"
              className="w-28 text-xs"
            />
          )}
          <span className="text-muted-foreground text-xs">then</span>
          <Select
            value={rule.action}
            onValueChange={(v) => updateRule(i, { action: v as LogicRule["action"] })}
          >
            <SelectTrigger className="w-28">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {LOGIC_ACTIONS.map((a) => (
                <SelectItem key={a.value} value={a.value}>
                  {a.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {fieldSelect(rule.target, (v) => updateRule(i, { target: v }))}
          <button
            type="button"
            onClick={() => removeRule(i)}
            className="ml-auto text-red-400 hover:text-red-600"
            aria-label={`Remove rule ${i + 1}`}
          >
            <TrashIcon className="h-4 w-4" />
          </button>
        </div>
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

export function FormBuilder({ schema, onSave, onChange }: FormBuilderProps) {
  const [fields, setFields] = useState<FieldDef[]>(() => schemaToFields(schema));
  const [logicRules, setLogicRules] = useState<LogicRule[]>(
    () => (schema["x-logic-rules"] as LogicRule[]) ?? []
  );
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set());

  const allExpanded = fields.length > 0 && fields.every((f) => expandedIds.has(f.id));
  const toggleExpanded = (id: string) => {
    setExpandedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };
  const toggleAllExpanded = () => {
    setExpandedIds(allExpanded ? new Set() : new Set(fields.map((f) => f.id)));
  };

  const buildSchema = () => {
    const built = fieldsToSchema(fields);
    if (logicRules.length > 0) built["x-logic-rules"] = logicRules;
    return built;
  };

  // Live preview: notify parent on every field/rule change
  const fieldsJson = JSON.stringify(fields);
  const rulesJson = JSON.stringify(logicRules);
  React.useEffect(() => {
    if (onChange) {
      onChange(buildSchema());
    }
  }, [fieldsJson, rulesJson]); // eslint-disable-line react-hooks/exhaustive-deps

  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates })
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
    onSave(buildSchema());
  };

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <div className="flex gap-2">
          <Button type="button" variant="outline" size="sm" onClick={addField}>
            <PlusIcon className="mr-1 h-3 w-3" /> Add Field
          </Button>
          <Button type="button" variant="ghost" size="sm" onClick={toggleAllExpanded}>
            {allExpanded ? (
              <ChevronUpIcon className="mr-1 h-3 w-3" />
            ) : (
              <ChevronDownIcon className="mr-1 h-3 w-3" />
            )}
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
                expanded={expandedIds.has(field.id)}
                onToggleExpanded={() => toggleExpanded(field.id)}
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

      <Separator />

      <LogicRulesEditor fields={fields} rules={logicRules} onChange={setLogicRules} />

      <div className="text-muted-foreground text-xs">
        Drag to reorder. Click ⚙ to configure type-specific settings.
        {fields.length > 0 && (
          <span>
            {" "}
            {fields.length} field{fields.length !== 1 ? "s" : ""},{" "}
            {fields.filter((f) => f.required).length} required.
          </span>
        )}
        {logicRules.length > 0 && (
          <span>
            {" "}
            {logicRules.length} logic rule{logicRules.length !== 1 ? "s" : ""}.
          </span>
        )}
      </div>
    </div>
  );
}
