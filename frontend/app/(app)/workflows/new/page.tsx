"use client";

import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { Loader2Icon, PlusIcon } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { useCreateWorkflow } from "@/graphql/workflows/workflows.hooks";

type FormValues = {
  name: string;
  slug: string;
  description: string;
  modelLabel: string;
};

export default function NewWorkflowPage() {
  const router = useRouter();
  const [createWorkflow] = useCreateWorkflow();

  const {
    register,
    handleSubmit,
    setValue,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({
    defaultValues: { name: "", slug: "", description: "", modelLabel: "" },
  });

  const autoSlug = (name: string) => {
    const slug = name
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-|-$/g, "");
    setValue("slug", slug);
  };

  const onSubmit = async (data: FormValues) => {
    const { data: result } = await createWorkflow({
      variables: {
        name: data.name,
        slug: data.slug,
        description: data.description || undefined,
        modelLabel: data.modelLabel,
        states: [],
        transitions: [],
      },
    });

    if (result?.createWorkflowDefinition?.ok) {
      toast.success("Workflow created", {
        description: `${data.name} is ready. Add states and transitions in the builder.`,
      });
      router.push(`/workflows/${data.slug}/builder`);
    } else {
      for (const e of result?.createWorkflowDefinition?.errors ?? []) {
        toast.error(`${e.field}: ${e.messages.join(", ")}`);
      }
    }
  };

  return (
    <div className="flex flex-1 flex-col gap-6 p-6">
      <div>
        <h1 className="text-xl font-semibold">Create New Workflow</h1>
        <p className="text-muted-foreground mt-1 text-sm">
          Define a new workflow definition, then configure states and transitions in the builder.
        </p>
      </div>
      <Separator />

      <form onSubmit={handleSubmit(onSubmit)} className="flex max-w-2xl flex-col gap-6">
        <div className="flex flex-col gap-1.5">
          <Label>Workflow Name</Label>
          <Input
            {...register("name", { required: "Name is required" })}
            placeholder="e.g. Approval Process"
            onChange={(e) => {
              register("name").onChange(e);
              autoSlug(e.target.value);
            }}
          />
          {errors.name && <p className="text-sm text-red-500">{errors.name.message}</p>}
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div className="flex flex-col gap-1.5">
            <Label>Slug</Label>
            <Input
              {...register("slug", { required: "Slug is required" })}
              placeholder="approval-process"
            />
            {errors.slug && <p className="text-sm text-red-500">{errors.slug.message}</p>}
          </div>
          <div className="flex flex-col gap-1.5">
            <Label>Model Label</Label>
            <Input
              {...register("modelLabel", { required: "Model label is required" })}
              placeholder="e.g. myapp.MyModel"
            />
            {errors.modelLabel && (
              <p className="text-sm text-red-500">{errors.modelLabel.message}</p>
            )}
          </div>
        </div>

        <div className="flex flex-col gap-1.5">
          <Label>Description</Label>
          <Textarea
            {...register("description")}
            placeholder="What does this workflow do?"
            rows={3}
          />
        </div>

        <Button type="submit" disabled={isSubmitting} className="self-start">
          {isSubmitting ? (
            <Loader2Icon className="mr-2 h-4 w-4 animate-spin" />
          ) : (
            <PlusIcon className="mr-2 h-4 w-4" />
          )}
          Create Workflow
        </Button>
      </form>
    </div>
  );
}
