"use client";

import {
  Button,
  EmptyState,
  ErrorState,
  LoadingState,
  PageHeader,
  StatusBadge,
} from "@calliopelabs/ui";
import Link from "next/link";
import { PlusIcon, TrashIcon, WrenchIcon } from "lucide-react";
import { toast } from "sonner";

import { Separator } from "@/ui-app/primitives/separator";
import { useConfirm } from "@/hooks/use-confirm";
import { useWorkflows, useDeleteWorkflow } from "@/graphql/workflows/workflows.hooks";
import type { WorkflowDefinition } from "@/graphql/workflows/workflows.types";

export default function WorkflowsPage() {
  const { workflows, loading, error } = useWorkflows();
  const [deleteWorkflow] = useDeleteWorkflow();
  const confirm = useConfirm();

  const handleDelete = async (wf: WorkflowDefinition) => {
    const ok = await confirm({
      title: `Delete "${wf.name}"?`,
      description: "This will permanently delete the workflow definition and cannot be undone.",
      confirmLabel: "Delete",
      cancelLabel: "Cancel",
    });
    if (!ok) return;

    const { data } = await deleteWorkflow({ variables: { slug: wf.slug } });
    if (data?.deleteWorkflowDefinition?.ok) {
      toast.success("Workflow deleted", { description: `${wf.name} has been removed.` });
    } else {
      for (const e of data?.deleteWorkflowDefinition?.errors ?? []) {
        toast.error(`${e.field}: ${e.messages.join(", ")}`);
      }
    }
  };

  return (
    <div className="flex flex-1 flex-col gap-6 p-6">
      <PageHeader
        title="Workflows"
        description="Manage workflow definitions and track active instances."
        primaryAction={
          <Button asChild size="sm">
            <Link href="/workflows/new">
              <PlusIcon /> New Workflow
            </Link>
          </Button>
        }
      />
      <Separator />

      {loading && workflows.length === 0 && <LoadingState label="Loading workflows" />}

      {error && <ErrorState title="Could not load workflows" error={error} />}

      {!loading && !error && workflows.length === 0 && (
        <EmptyState
          title="No workflows defined yet"
          description="A workflow is a state machine you attach to a model."
          actionHref="/workflows/new"
          actionLabel="Create your first workflow"
        />
      )}

      <div className="grid gap-4">
        {workflows.map((wf) => (
          <div key={wf.slug} className="flex items-center justify-between rounded-lg border p-4">
            <div className="flex flex-col gap-1">
              <div className="flex items-center gap-2">
                <span className="font-medium">{wf.name}</span>
                <StatusBadge tone={wf.isEnabled ? "ok" : "muted"}>
                  {wf.isEnabled ? "Active" : "Disabled"}
                </StatusBadge>
                <span className="text-muted-foreground text-xs">{wf.modelLabel}</span>
              </div>
              <span className="text-muted-foreground text-sm">
                {wf.description || "No description"}
              </span>
            </div>
            <div className="flex items-center gap-4">
              <div className="text-muted-foreground text-sm">
                {wf.activeInstanceCount} active / {wf.instanceCount} total
              </div>
              <Button variant="outline" size="sm" asChild>
                <Link href={`/workflows/${wf.slug}/builder`}>
                  <WrenchIcon className="mr-1 h-3 w-3" /> Builder
                </Link>
              </Button>
              <Button variant="outline" size="sm" onClick={() => handleDelete(wf)}>
                <TrashIcon className="mr-1 h-3 w-3" /> Delete
              </Button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
