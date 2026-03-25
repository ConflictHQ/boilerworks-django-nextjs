export type WorkflowState = {
  name: string;
  label: string;
  is_initial: boolean;
  is_final: boolean;
  color: string;
};

export type WorkflowTransition = {
  from_state: string;
  to_state: string;
  label: string;
  conditions: unknown[];
  actions: unknown[];
};

export type WorkflowDefinition = {
  name: string;
  slug: string;
  description: string | null;
  modelLabel: string;
  states: WorkflowState[];
  transitions: WorkflowTransition[];
  isEnabled: boolean;
  createdAt: string;
  instanceCount: number;
  activeInstanceCount: number;
};

export type WorkflowDefinitionsData = {
  workflowDefinitions: WorkflowDefinition[];
};

export type WorkflowDefinitionData = {
  workflowDefinition: WorkflowDefinition | null;
};

export type MutationError = {
  field: string;
  messages: string[];
};

export type WorkflowMutationResult = {
  ok: boolean;
  errors: MutationError[];
};

export type CreateWorkflowData = {
  createWorkflowDefinition: WorkflowMutationResult;
};

export type UpdateWorkflowData = {
  updateWorkflowDefinition: WorkflowMutationResult;
};

export type DeleteWorkflowData = {
  deleteWorkflowDefinition: WorkflowMutationResult;
};

export type StartWorkflowData = {
  startWorkflow: WorkflowMutationResult & {
    instanceId: string | null;
  };
};

export type TransitionWorkflowData = {
  transitionWorkflow: WorkflowMutationResult;
};
