"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { Loader2Icon, PlusIcon, CodeIcon, LayoutIcon } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { useCreateFormDefinition } from "@/graphql/forms/forms.hooks";
import { FormBuilder } from "@/components/forms/FormBuilder";

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
  const [schema, setSchema] = useState<Record<string, unknown>>(DEFAULT_SCHEMA);
  const [jsonText, setJsonText] = useState(JSON.stringify(DEFAULT_SCHEMA, null, 2));

  const {
    register,
    handleSubmit,
    setValue,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({
    defaultValues: { name: "", slug: "", description: "" },
  });

  const autoSlug = (name: string) => {
    const slug = name
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-|-$/g, "");
    setValue("slug", slug);
  };

  const onSubmit = async (data: FormValues) => {
    let finalSchema: Record<string, unknown>;
    if (mode === "json") {
      try {
        finalSchema = JSON.parse(jsonText);
      } catch {
        toast.error("Invalid JSON schema");
        return;
      }
    } else {
      finalSchema = schema;
    }

    const { data: result } = await createForm({
      variables: {
        input: {
          name: data.name,
          slug: data.slug,
          description: data.description,
          schema: finalSchema,
        },
      },
    });

    if (result?.createFormDefinition?.ok) {
      toast.success("Form created", { description: `${data.name} is ready as a draft.` });
      router.push(`/forms/${data.slug}`);
    } else {
      const errs = result?.createFormDefinition?.errors ?? [];
      for (const e of errs) {
        toast.error(`${e.field}: ${e.messages.join(", ")}`);
      }
    }
  };

  return (
    <div className="flex flex-1 flex-col gap-6 p-6">
      <div>
        <h1 className="text-xl font-semibold">Create New Form</h1>
        <p className="text-muted-foreground mt-1 text-sm">
          Define a new form with fields, validation, and settings.
        </p>
      </div>
      <Separator />

      <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-6">
        <div className="grid max-w-2xl gap-4">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="name">Name</Label>
            <Input
              {...register("name", { required: "Name is required" })}
              placeholder="e.g. Expense Report"
              onChange={(e) => {
                register("name").onChange(e);
                autoSlug(e.target.value);
              }}
            />
            {errors.name && <p className="text-sm text-red-500">{errors.name.message}</p>}
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="slug">Slug</Label>
              <Input {...register("slug", { required: "Slug is required" })} placeholder="expense-report" />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="description">Description</Label>
              <Input {...register("description")} placeholder="What is this form for?" />
            </div>
          </div>
        </div>

        <div>
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-lg font-semibold">Form Fields</h2>
            <div className="flex gap-1 rounded-lg border p-0.5">
              <button
                type="button"
                onClick={() => {
                  if (mode === "json") {
                    try { setSchema(JSON.parse(jsonText)); } catch { /* keep current */ }
                  }
                  setMode("visual");
                }}
                className={`flex items-center gap-1 rounded-md px-3 py-1 text-sm ${mode === "visual" ? "bg-primary text-primary-foreground" : ""}`}
              >
                <LayoutIcon className="h-3 w-3" /> Visual
              </button>
              <button
                type="button"
                onClick={() => {
                  setJsonText(JSON.stringify(schema, null, 2));
                  setMode("json");
                }}
                className={`flex items-center gap-1 rounded-md px-3 py-1 text-sm ${mode === "json" ? "bg-primary text-primary-foreground" : ""}`}
              >
                <CodeIcon className="h-3 w-3" /> JSON
              </button>
            </div>
          </div>

          {mode === "visual" ? (
            <FormBuilder schema={schema} onSave={(s) => setSchema(s)} />
          ) : (
            <Textarea
              value={jsonText}
              onChange={(e) => setJsonText(e.target.value)}
              rows={16}
              className="font-mono text-sm"
            />
          )}
        </div>

        <Button type="submit" disabled={isSubmitting} className="self-start">
          {isSubmitting ? (
            <Loader2Icon className="mr-2 h-4 w-4 animate-spin" />
          ) : (
            <PlusIcon className="mr-2 h-4 w-4" />
          )}
          Create Form
        </Button>
      </form>
    </div>
  );
}
