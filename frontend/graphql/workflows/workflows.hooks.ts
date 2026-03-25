import { useMutation, useQuery } from "@apollo/client/react";

import { GET_WORKFLOW, GET_WORKFLOWS } from "./workflows.queries";
import {
  CREATE_WORKFLOW,
  DELETE_WORKFLOW,
  START_WORKFLOW,
  TRANSITION_WORKFLOW,
  UPDATE_WORKFLOW,
} from "./workflows.mutations";
import type {
  CreateWorkflowData,
  DeleteWorkflowData,
  StartWorkflowData,
  TransitionWorkflowData,
  UpdateWorkflowData,
  WorkflowDefinitionData,
  WorkflowDefinitionsData,
} from "./workflows.types";

export const useWorkflows = (modelLabel?: string) => {
  const { data, loading, error, refetch } = useQuery<WorkflowDefinitionsData>(GET_WORKFLOWS, {
    variables: { modelLabel },
    fetchPolicy: "cache-and-network",
  });
  return { workflows: data?.workflowDefinitions ?? [], loading, error, refetch };
};

export const useWorkflow = (slug: string) => {
  const { data, loading, error, refetch } = useQuery<WorkflowDefinitionData>(GET_WORKFLOW, {
    variables: { slug },
    fetchPolicy: "cache-and-network",
    skip: !slug,
  });
  return { workflow: data?.workflowDefinition ?? null, loading, error, refetch };
};

export const useCreateWorkflow = () =>
  useMutation<CreateWorkflowData>(CREATE_WORKFLOW, {
    refetchQueries: [GET_WORKFLOWS],
  });

export const useUpdateWorkflow = () =>
  useMutation<UpdateWorkflowData>(UPDATE_WORKFLOW, {
    refetchQueries: [GET_WORKFLOWS],
  });

export const useDeleteWorkflow = () =>
  useMutation<DeleteWorkflowData>(DELETE_WORKFLOW, {
    refetchQueries: [GET_WORKFLOWS],
  });

export const useStartWorkflow = () => useMutation<StartWorkflowData>(START_WORKFLOW);

export const useTransitionWorkflow = () => useMutation<TransitionWorkflowData>(TRANSITION_WORKFLOW);
