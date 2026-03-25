import { gql } from "@apollo/client";

export const CREATE_WORKFLOW = gql`
  mutation CreateWorkflowDefinition(
    $name: String!
    $slug: String!
    $modelLabel: String!
    $states: JSON!
    $transitions: JSON!
    $description: String
    $isEnabled: Boolean
  ) {
    createWorkflowDefinition(
      name: $name
      slug: $slug
      modelLabel: $modelLabel
      states: $states
      transitions: $transitions
      description: $description
      isEnabled: $isEnabled
    ) {
      ok
      errors {
        field
        messages
      }
    }
  }
`;

export const UPDATE_WORKFLOW = gql`
  mutation UpdateWorkflowDefinition(
    $slug: String!
    $name: String
    $description: String
    $modelLabel: String
    $states: JSON
    $transitions: JSON
    $isEnabled: Boolean
  ) {
    updateWorkflowDefinition(
      slug: $slug
      name: $name
      description: $description
      modelLabel: $modelLabel
      states: $states
      transitions: $transitions
      isEnabled: $isEnabled
    ) {
      ok
      errors {
        field
        messages
      }
    }
  }
`;

export const DELETE_WORKFLOW = gql`
  mutation DeleteWorkflowDefinition($slug: String!) {
    deleteWorkflowDefinition(slug: $slug) {
      ok
      errors {
        field
        messages
      }
    }
  }
`;

export const START_WORKFLOW = gql`
  mutation StartWorkflow($workflowSlug: String!, $modelLabel: String!, $objectId: Int!) {
    startWorkflow(workflowSlug: $workflowSlug, modelLabel: $modelLabel, objectId: $objectId) {
      ok
      instanceId
      errors {
        field
        messages
      }
    }
  }
`;

export const TRANSITION_WORKFLOW = gql`
  mutation TransitionWorkflow($instanceId: ID!, $toState: String!, $note: String) {
    transitionWorkflow(instanceId: $instanceId, toState: $toState, note: $note) {
      ok
      errors {
        field
        messages
      }
    }
  }
`;
