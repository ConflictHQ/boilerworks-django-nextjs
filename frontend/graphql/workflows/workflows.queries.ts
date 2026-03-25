import { gql } from "@apollo/client";

export const GET_WORKFLOWS = gql`
  query GetWorkflows($modelLabel: String) {
    workflowDefinitions(modelLabel: $modelLabel) {
      name
      slug
      description
      modelLabel
      isEnabled
      createdAt
      instanceCount
      activeInstanceCount
    }
  }
`;

export const GET_WORKFLOW = gql`
  query GetWorkflow($slug: String!) {
    workflowDefinition(slug: $slug) {
      name
      slug
      description
      modelLabel
      states
      transitions
      isEnabled
      createdAt
      instanceCount
      activeInstanceCount
    }
  }
`;
