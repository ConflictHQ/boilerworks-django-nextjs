"use client";

import Link from "next/link";
import { Loader2Icon, WrenchIcon } from "lucide-react";
import { useQuery } from "@apollo/client/react";
import { gql } from "@apollo/client";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

const GET_WORKFLOWS = gql`
  query GetWorkflows {
    workflowDefinitions {
      name
      slug
      description
      modelLabel
      isEnabled
      instanceCount
      activeInstanceCount
    }
  }
`;

export default function WorkflowsPage() {
  const { data, loading, error } = useQuery(GET_WORKFLOWS, { fetchPolicy: "cache-and-network" });
  const workflows = data?.workflowDefinitions ?? [];

  return (
    <div className="flex flex-1 flex-col gap-6 p-6">
      <div>
        <h1 className="text-xl font-semibold">Workflows</h1>
        <p className="text-muted-foreground mt-1 text-sm">
          Manage workflow definitions and track active instances.
        </p>
      </div>
      <Separator />

      {loading && (
        <div className="flex items-center justify-center p-12">
          <Loader2Icon className="text-muted-foreground h-6 w-6 animate-spin" />
        </div>
      )}

      {error && (
        <div className="rounded-md bg-red-50 p-4 text-red-800">
          Error: {error.message}
        </div>
      )}

      {!loading && workflows.length === 0 && (
        <div className="text-muted-foreground py-12 text-center">
          No workflows defined yet. Create one in the Django admin.
        </div>
      )}

      <div className="grid gap-4">
        {workflows.map((wf: Record<string, unknown>) => (
          <div
            key={wf.slug as string}
            className="flex items-center justify-between rounded-lg border p-4"
          >
            <div className="flex flex-col gap-1">
              <div className="flex items-center gap-2">
                <span className="font-medium">{wf.name as string}</span>
                <Badge variant={wf.isEnabled ? "default" : "secondary"}>
                  {wf.isEnabled ? "Active" : "Disabled"}
                </Badge>
                <span className="text-muted-foreground text-xs">{wf.modelLabel as string}</span>
              </div>
              <span className="text-muted-foreground text-sm">{(wf.description as string) || "No description"}</span>
            </div>
            <div className="flex items-center gap-4">
              <div className="text-muted-foreground text-sm">
                {wf.activeInstanceCount as number} active / {wf.instanceCount as number} total
              </div>
              <Button variant="outline" size="sm" asChild>
                <Link href={`/workflows/${wf.slug}/builder`}>
                  <WrenchIcon className="mr-1 h-3 w-3" /> Builder
                </Link>
              </Button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
