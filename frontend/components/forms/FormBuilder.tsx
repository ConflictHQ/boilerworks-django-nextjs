"use client";

import { useState } from "react";
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
import { GripVerticalIcon, PlusIcon, SaveIcon, TrashIcon, SettingsIcon } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";

const FIELD_TYPES = [
  { value: "text", label: "Text" },
  { value: "textarea", label: "Textarea" },
  { value: "number", label: "Number" },
  { value: "integer", label: "Integer" },
  { value: "boolean", label: "Checkbox" },
  { value: "date", label: "Date" },
  { value: "datetime", label: "Date & Time" },
  { value: "email", label: "Email" },
  { value: "url", label: "URL" },
  { value: "select", label: "Dropdown" },
  { value: "multi_select", label: "Multi-Select" },
  { value: "rating", label: "Rating (Stars)" },
  { value: "scale", label: "Scale (Slider)" },
  { value: "file", label: "File Upload" },
  { value: "signature", label: "Signature" },
  { value: "repeatable", label: "Repeatable Section" },
  { value: "percentage_split", label: "Percentage Split" },
];

type FieldDef = {
  id: string;
  name: string;
  type: string;
  title: string;
  required: boolean;
  description: string;
  options: string; // comma-separated for select/multi_select
};

type FormBuilderProps = {
  schema: Record<string, unknown>;
  onSave: (schema: Record<string, unknown>) => void;
};

function SortableField({
  field,
  onUpdate,
  onRemove,
}: {
  field: FieldDef;
  onUpdate: (field: FieldDef) => void;
  onRemove: () => void;
}) {
  const [expanded, setExpanded] = useState(false);
  const { attributes, listeners, setNodeRef, transform, transition } = useSortable({ id: field.id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  };

  return (
    <div ref={setNodeRef} style={style} className="rounded-lg border bg-white p-3 dark:bg-gray-900">
      <div className="flex items-center gap-2">
        <button {...attributes} {...listeners} className="cursor-grab text-gray-400 hover:text-gray-600">
          <GripVerticalIcon className="h-4 w-4" />
        </button>
        <Input
          value={field.title}
          onChange={(e) => onUpdate({ ...field, title: e.target.value })}
          className="flex-1 border-none bg-transparent p-0 font-medium shadow-none focus-visible:ring-0"
          placeholder="Field label"
        />
        <Select value={field.type} onValueChange={(v) => onUpdate({ ...field, type: v })}>
          <SelectTrigger className="w-36">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {FIELD_TYPES.map((ft) => (
              <SelectItem key={ft.value} value={ft.value}>
                {ft.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <label className="flex items-center gap-1 text-xs">
          <input
            type="checkbox"
            checked={field.required}
            onChange={(e) => onUpdate({ ...field, required: e.target.checked })}
            className="h-3 w-3"
          />
          Req
        </label>
        <button onClick={() => setExpanded(!expanded)} className="text-gray-400 hover:text-gray-600">
          <SettingsIcon className="h-4 w-4" />
        </button>
        <button onClick={onRemove} className="text-red-400 hover:text-red-600">
          <TrashIcon className="h-4 w-4" />
        </button>
      </div>

      {expanded && (
        <div className="mt-3 grid gap-2 border-t pt-3">
          <div className="grid grid-cols-2 gap-2">
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
              <Input
                value={field.description}
                onChange={(e) => onUpdate({ ...field, description: e.target.value })}
                className="text-xs"
              />
            </div>
          </div>
          {(field.type === "select" || field.type === "multi_select") && (
            <div>
              <Label className="text-xs">Options (comma-separated)</Label>
              <Input
                value={field.options}
                onChange={(e) => onUpdate({ ...field, options: e.target.value })}
                placeholder="Option A, Option B, Option C"
                className="text-xs"
              />
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function schemaToFields(schema: Record<string, unknown>): FieldDef[] {
  const properties = (schema.properties || {}) as Record<string, Record<string, unknown>>;
  const required = new Set((schema.required || []) as string[]);
  return Object.entries(properties).map(([name, def], i) => ({
    id: `field-${i}`,
    name,
    type: resolveType(def),
    title: (def.title as string) || name.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase()),
    required: required.has(name),
    description: (def.description as string) || "",
    options: (def.enum as string[])?.join(", ") || "",
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
    const ft = FIELD_TYPES.find((t) => t.value === field.type);

    // Map type
    switch (field.type) {
      case "text": case "textarea": case "email": case "url": case "date": case "datetime": case "signature":
        prop.type = "string"; break;
      case "number": prop.type = "number"; break;
      case "integer": case "rating": case "scale": prop.type = "integer"; break;
      case "boolean": prop.type = "boolean"; break;
      case "select": prop.type = "string"; break;
      case "multi_select": case "repeatable": prop.type = "array"; break;
      case "percentage_split": prop.type = "object"; break;
      default: prop.type = "string";
    }

    if (field.type === "email") prop.format = "email";
    if (field.type === "url") prop.format = "uri";
    if (field.type === "date") prop.format = "date";
    if (field.type === "datetime") prop.format = "date-time";
    if (field.type === "textarea") prop["x-widget"] = "textarea";
    if (field.type === "rating") { prop["x-widget"] = "rating"; prop.minimum = 1; prop.maximum = 5; }
    if (field.type === "scale") { prop["x-widget"] = "scale"; prop.minimum = 0; prop.maximum = 10; }
    if (field.type === "signature") prop["x-widget"] = "signature";
    if (field.type === "file") { prop.format = "uri"; prop["x-widget"] = "file"; }

    if (field.options && (field.type === "select" || field.type === "multi_select")) {
      const opts = field.options.split(",").map((o) => o.trim()).filter(Boolean);
      if (field.type === "select") prop.enum = opts;
      else prop.items = { type: "string", enum: opts };
    }

    if (field.title) prop.title = field.title;
    if (field.description) prop.description = field.description;

    properties[field.name] = prop;
    if (field.required) required.push(field.name);
  }

  return { type: "object", properties, required };
}

export function FormBuilder({ schema, onSave }: FormBuilderProps) {
  const [fields, setFields] = useState<FieldDef[]>(() => schemaToFields(schema));

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
    const index = fields.length;
    setFields((prev) => [
      ...prev,
      {
        id: `field-${Date.now()}`,
        name: `field_${index + 1}`,
        type: "text",
        title: `Field ${index + 1}`,
        required: false,
        description: "",
        options: "",
      },
    ]);
  };

  const updateField = (id: string, updated: FieldDef) => {
    setFields((prev) => prev.map((f) => (f.id === id ? updated : f)));
  };

  const removeField = (id: string) => {
    setFields((prev) => prev.filter((f) => f.id !== id));
  };

  const handleSave = () => {
    onSave(fieldsToSchema(fields));
  };

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <Button variant="outline" size="sm" onClick={addField}>
          <PlusIcon className="mr-1 h-3 w-3" /> Add Field
        </Button>
        <Button size="sm" onClick={handleSave}>
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
      <div className="text-muted-foreground text-xs">
        Drag fields to reorder. Click the gear icon to expand field settings.
        {fields.length > 0 && <span> {fields.length} fields, {fields.filter((f) => f.required).length} required.</span>}
      </div>
    </div>
  );
}
