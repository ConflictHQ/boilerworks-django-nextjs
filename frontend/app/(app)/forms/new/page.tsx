"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { Loader2Icon, PlusIcon, CodeIcon, LayoutIcon, EyeIcon, EyeOffIcon, GripVerticalIcon } from "lucide-react";
import { Panel, Group as PanelGroup, Separator as PanelResizeHandle } from "react-resizable-panels";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { useCreateFormDefinition } from "@/graphql/forms/forms.hooks";
import { FormBuilder } from "@/components/forms/FormBuilder";
import { FormPreview } from "@/components/forms/FormPreview";

type FormValues = {
  name: string;
  slug: string;
  description: string;
};

const DEFAULT_SCHEMA = {
  type: "object",
  properties: { name: { type: "string", title: "Name" } },
  required: ["name"],
};

export default function NewFormPage() {
  const router = useRouter();
  const [createForm] = useCreateFormDefinition();
  const [mode, setMode] = useState<"visual" | "json">("visual");
  const [showPreview, setShowPreview] = useState(true);
  const [schema, setSchema] = useState<Record<string, unknown>>(DEFAULT_SCHEMA);
  const [liveSchema, setLiveSchema] = useState<Record<string, unknown>>(DEFAULT_SCHEMA);
  const [jsonText, setJsonText] = useState(JSON.stringify(DEFAULT_SCHEMA, null, 2));

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({
    defaultValues: { name: "", slug: "", description: "" },
  });

  const nameValue = watch("name");

  const autoSlug = (name: string) => {
    const slug = name.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
    setValue("slug", slug);
  };

  const onSubmit = async (data: FormValues) => {
    let finalSchema: Record<string, unknown>;
    if (mode === "json") {
      try { finalSchema = JSON.parse(jsonText); } catch { toast.error("Invalid JSON schema"); return; }
    } else {
      finalSchema = schema;
    }

    const { data: result } = await createForm({
      variables: { input: { name: data.name, slug: data.slug, description: data.description, schema: finalSchema } },
    });

    if (result?.createFormDefinition?.ok) {
      toast.success("Form created", { description: `${data.name} is ready as a draft.` });
      router.push(`/forms/${data.slug}`);
    } else {
      for (const e of result?.createFormDefinition?.errors ?? []) {
        toast.error(`${e.field}: ${e.messages.join(", ")}`);
      }
    }
  };

  return (
    <div className="flex flex-1 overflow-hidden">
      {/* Full-height resizable split */}
      <PanelGroup direction="horizontal" className="flex-1">
        <Panel defaultSize={showPreview ? 65 : 100} minSize={40}>
        {/* LEFT PANE: scrollable form + builder */}
        <form onSubmit={handleSubmit(onSubmit)} className="flex h-full flex-col gap-6 overflow-y-auto p-6">
          {/* Header */}
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-xl font-semibold">Create New Form</h1>
              <p className="text-muted-foreground mt-1 text-sm">
                Define fields, configure validation, see a live preview.
              </p>
            </div>
            <button
              type="button"
              onClick={() => setShowPreview(!showPreview)}
              className={`flex items-center gap-1 rounded-md border px-3 py-1.5 text-sm ${showPreview ? "bg-primary text-primary-foreground" : ""}`}
            >
              {showPreview ? <EyeOffIcon className="h-3 w-3" /> : <EyeIcon className="h-3 w-3" />}
              {showPreview ? "Hide" : "Preview"}
            </button>
          </div>
          <Separator />

          {/* Metadata */}
          <div className="grid gap-4">
            <div className="flex flex-col gap-1.5">
              <Label>Form Name</Label>
              <Input
                {...register("name", { required: "Name is required" })}
                placeholder="e.g. Expense Report"
                onChange={(e) => { register("name").onChange(e); autoSlug(e.target.value); }}
              />
              {errors.name && <p className="text-sm text-red-500">{errors.name.message}</p>}
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="flex flex-col gap-1.5">
                <Label>Slug</Label>
                <Input {...register("slug", { required: "Slug is required" })} placeholder="expense-report" />
              </div>
              <div className="flex flex-col gap-1.5">
                <Label>Description</Label>
                <Input {...register("description")} placeholder="What is this form for?" />
              </div>
            </div>
          </div>

          <Separator />

          {/* Mode toggle */}
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold">Form Fields</h2>
            <div className="flex gap-1 rounded-lg border p-0.5">
              <button
                type="button"
                onClick={() => {
                  if (mode === "json") { try { const s = JSON.parse(jsonText); setSchema(s); setLiveSchema(s); } catch {} }
                  setMode("visual");
                }}
                className={`flex items-center gap-1 rounded-md px-3 py-1 text-sm ${mode === "visual" ? "bg-primary text-primary-foreground" : ""}`}
              >
                <LayoutIcon className="h-3 w-3" /> Visual
              </button>
              <button
                type="button"
                onClick={() => { setJsonText(JSON.stringify(liveSchema, null, 2)); setMode("json"); }}
                className={`flex items-center gap-1 rounded-md px-3 py-1 text-sm ${mode === "json" ? "bg-primary text-primary-foreground" : ""}`}
              >
                <CodeIcon className="h-3 w-3" /> JSON
              </button>
            </div>
          </div>

          {mode === "visual" ? (
            <FormBuilder
              schema={schema}
              onSave={(s) => { setSchema(s); setLiveSchema(s); }}
              onChange={(s) => setLiveSchema(s)}
            />
          ) : (
            <Textarea
              value={jsonText}
              onChange={(e) => {
                setJsonText(e.target.value);
                try { setLiveSchema(JSON.parse(e.target.value)); } catch {}
              }}
              rows={24}
              className="font-mono text-sm"
            />
          )}

          <Button type="submit" disabled={isSubmitting} className="self-start">
            {isSubmitting ? <Loader2Icon className="mr-2 h-4 w-4 animate-spin" /> : <PlusIcon className="mr-2 h-4 w-4" />}
            Create Form
          </Button>
        </form>
        </Panel>

        {/* RESIZE HANDLE + RIGHT PANE */}
        {showPreview && (
          <>
            <PanelResizeHandle className="flex w-2 items-center justify-center bg-border/50 hover:bg-border transition-colors">
              <GripVerticalIcon className="h-4 w-4 text-muted-foreground" />
            </PanelResizeHandle>
            <Panel defaultSize={35} minSize={20}>
              <div className="h-full overflow-y-auto bg-muted/30 p-6">
                <h2 className="mb-4 text-sm font-semibold uppercase tracking-wider text-muted-foreground">Live Preview</h2>
                <div className="rounded-lg border bg-background p-4 shadow-sm">
                  <FormPreview schema={liveSchema} formName={nameValue || "Untitled Form"} />
                </div>
              </div>
            </Panel>
          </>
        )}
      </PanelGroup>
    </div>
  );
}
