"use client";

import { useParams } from "next/navigation";
import { Loader2Icon } from "lucide-react";
import { toast } from "sonner";

import { Separator } from "@/components/ui/separator";
import { WorkflowBuilder } from "@/components/workflows/WorkflowBuilder";
import { useWorkflow, useUpdateWorkflow } from "@/graphql/workflows/workflows.hooks";
import { useFormDefinitions } from "@/graphql/forms/forms.hooks";
import type { WorkflowState, WorkflowTransition } from "@/graphql/workflows/workflows.types";

export default function WorkflowBuilderPage() {
  const { slug } = useParams<{ slug: string }>();
  const { workflow, loading, error, refetch } = useWorkflow(slug);
  const [updateWorkflow] = useUpdateWorkflow();
  const { forms } = useFormDefinitions("published");

  if (loading && !workflow) {
    return (
      <div className="flex flex-1 items-center justify-center p-6">
        <Loader2Icon className="text-muted-foreground h-6 w-6 animate-spin" />
      </div>
    );
  }

  if (error || !workflow) {
    return (
      <div className="flex flex-1 flex-col gap-6 p-6">
        <div className="rounded-md bg-red-50 p-4 text-red-800">
          {error ? `Error: ${error.message}` : `Workflow "${slug}" not found`}
        </div>
      </div>
    );
  }

  const handleSave = async (states: WorkflowState[], transitions: WorkflowTransition[]) => {
    const { data } = await updateWorkflow({
      variables: { slug, states, transitions },
    });

    if (data?.updateWorkflowDefinition?.ok) {
      toast.success("Workflow saved", {
        description: `${states.length} states, ${transitions.length} transitions`,
      });
      refetch();
    } else {
      const errors = data?.updateWorkflowDefinition?.errors ?? [];
      if (errors.length > 0) {
        for (const e of errors) {
          toast.error(`${e.field}: ${e.messages.join(", ")}`);
        }
      } else {
        toast.error("Failed to save workflow");
      }
    }
  };

  return (
    <div className="flex flex-1 flex-col gap-6 p-6">
      <div>
        <h1 className="text-xl font-semibold">{workflow.name} — Builder</h1>
        <p className="text-muted-foreground mt-1 text-sm">
          Drag states, draw transitions. Click Save to update the workflow.
        </p>
      </div>
      <Separator />
      <WorkflowBuilder
        states={workflow.states || []}
        transitions={workflow.transitions || []}
        onSave={handleSave}
        availableForms={(forms ?? []).map((f: { slug: string; name: string }) => ({ slug: f.slug, name: f.name }))}
      />
    </div>
  );
}
