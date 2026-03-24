import { gql } from "@apollo/client";

export const GET_FORM_DEFINITIONS = gql`
  query GetFormDefinitions($status: String) {
    formDefinitions(status: $status) {
      name
      slug
      description
      status
      version
      formType
      isPublic
      publishedAt
      createdAt
      updatedAt
      submissionCount
    }
  }
`;

export const GET_FORM_DEFINITION = gql`
  query GetFormDefinition($slug: String!) {
    formDefinition(slug: $slug) {
      name
      slug
      description
      status
      version
      schema
      formType
      isPublic
      fieldConfig
      logicRules
      scoring
      publishedAt
      createdAt
      updatedAt
      submissionCount
    }
  }
`;

export const GET_FORM_SUBMISSIONS = gql`
  query GetFormSubmissions($slug: String!, $status: String) {
    formSubmissions(slug: $slug, status: $status) {
      payload
      status
      submittedAt
      createdAt
      formName
      formVersion
      formSlug
    }
  }
`;

export const GET_FORM_FIELD_TYPES = gql`
  query GetFormFieldTypes {
    formFieldTypes
  }
`;
