"use client";

import Link from "next/link";
import { Loader2Icon, PlusIcon, TrashIcon, WrenchIcon } from "lucide-react";
import { toast } from "sonner";

import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
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
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold">Workflows</h1>
          <p className="text-muted-foreground mt-1 text-sm">
            Manage workflow definitions and track active instances.
          </p>
        </div>
        <Button asChild>
          <Link href="/workflows/new">
            <PlusIcon className="mr-1 h-4 w-4" /> New Workflow
          </Link>
        </Button>
      </div>
      <Separator />

      {loading && (
        <div className="flex items-center justify-center p-12">
          <Loader2Icon className="text-muted-foreground h-6 w-6 animate-spin" />
        </div>
      )}

      {error && <div className="rounded-md bg-red-50 p-4 text-red-800">Error: {error.message}</div>}

      {!loading && workflows.length === 0 && (
        <div className="text-muted-foreground flex flex-col items-center gap-3 py-12 text-center">
          <p>No workflows defined yet.</p>
          <Button variant="outline" asChild>
            <Link href="/workflows/new">
              <PlusIcon className="mr-1 h-4 w-4" /> Create your first workflow
            </Link>
          </Button>
        </div>
      )}

      <div className="grid gap-4">
        {workflows.map((wf) => (
          <div key={wf.slug} className="flex items-center justify-between rounded-lg border p-4">
            <div className="flex flex-col gap-1">
              <div className="flex items-center gap-2">
                <span className="font-medium">{wf.name}</span>
                <Badge variant={wf.isEnabled ? "default" : "secondary"}>
                  {wf.isEnabled ? "Active" : "Disabled"}
                </Badge>
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
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleDelete(wf)}
                className="text-red-600 hover:text-red-700"
              >
                <TrashIcon className="mr-1 h-3 w-3" /> Delete
              </Button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
