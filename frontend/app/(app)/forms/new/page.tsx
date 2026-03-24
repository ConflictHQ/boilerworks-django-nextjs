"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { Loader2Icon, PlusIcon } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useCreateFormDefinition } from "@/graphql/forms/forms.hooks";

type FormValues = {
  name: string;
  slug: string;
  description: string;
  formType: string;
};

export default function NewFormPage() {
  const router = useRouter();
  const [createForm] = useCreateFormDefinition();
  const [schemaText, setSchemaText] = useState(
    JSON.stringify(
      {
        type: "object",
        properties: {
          name: { type: "string", title: "Name" },
        },
        required: ["name"],
      },
      null,
      2,
    ),
  );

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({
    defaultValues: { name: "", slug: "", description: "", formType: "standard" },
  });

  const nameValue = watch("name");

  const autoSlug = (name: string) => {
    const slug = name
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-|-$/g, "");
    setValue("slug", slug);
  };

  const onSubmit = async (data: FormValues) => {
    let schema: Record<string, unknown>;
    try {
      schema = JSON.parse(schemaText);
    } catch {
      toast.error("Invalid JSON schema");
      return;
    }

    const { data: result } = await createForm({
      variables: {
        input: {
          name: data.name,
          slug: data.slug,
          description: data.description,
          schema,
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

      <form onSubmit={handleSubmit(onSubmit)} className="flex max-w-2xl flex-col gap-4">
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

        <div className="flex flex-col gap-1.5">
          <Label htmlFor="slug">Slug</Label>
          <Input {...register("slug", { required: "Slug is required" })} placeholder="expense-report" />
          {errors.slug && <p className="text-sm text-red-500">{errors.slug.message}</p>}
        </div>

        <div className="flex flex-col gap-1.5">
          <Label htmlFor="description">Description</Label>
          <Input {...register("description")} placeholder="What is this form for?" />
        </div>

        <div className="flex flex-col gap-1.5">
          <Label>Schema (JSON)</Label>
          <Textarea
            value={schemaText}
            onChange={(e) => setSchemaText(e.target.value)}
            rows={12}
            className="font-mono text-sm"
            placeholder='{"type": "object", "properties": {...}}'
          />
          <p className="text-muted-foreground text-xs">
            Define form fields using JSON Schema. Each property becomes a form field.
          </p>
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
