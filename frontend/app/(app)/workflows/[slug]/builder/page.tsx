"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import { Loader2Icon } from "lucide-react";
import { toast } from "sonner";
import { useQuery, useMutation } from "@apollo/client/react";
import { gql } from "@apollo/client";

import { Separator } from "@/components/ui/separator";
import { WorkflowBuilder } from "@/components/workflows/WorkflowBuilder";

const GET_WORKFLOW = gql`
  query GetWorkflow($slug: String!) {
    workflowDefinition(slug: $slug) {
      name
      slug
      states
      transitions
    }
  }
`;

// For now, use a simple mutation — TODO: add proper updateWorkflow mutation
const UPDATE_WORKFLOW = gql`
  mutation UpdateWorkflow($slug: String!, $states: JSON!, $transitions: JSON!) {
    __typename
  }
`;

export default function WorkflowBuilderPage() {
  const { slug } = useParams<{ slug: string }>();
  const { data, loading, error } = useQuery(GET_WORKFLOW, {
    variables: { slug },
    fetchPolicy: "cache-and-network",
  });

  if (loading) {
    return (
      <div className="flex flex-1 items-center justify-center p-6">
        <Loader2Icon className="text-muted-foreground h-6 w-6 animate-spin" />
      </div>
    );
  }

  const workflow = data?.workflowDefinition;
  if (error || !workflow) {
    return (
      <div className="flex flex-1 flex-col gap-6 p-6">
        <div className="rounded-md bg-red-50 p-4 text-red-800">
          {error ? `Error: ${error.message}` : `Workflow "${slug}" not found`}
        </div>
      </div>
    );
  }

  const handleSave = (states: unknown[], transitions: unknown[]) => {
    // TODO: wire to real mutation when updateWorkflow is added
    toast.success("Workflow saved", {
      description: `${(states as unknown[]).length} states, ${(transitions as unknown[]).length} transitions`,
    });
    console.log("Workflow output:", { states, transitions });
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
      />
    </div>
  );
}
