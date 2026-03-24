import { gql } from "@apollo/client";

export const CREATE_FORM_DEFINITION = gql`
  mutation CreateFormDefinition($input: FormDefinitionInput!) {
    createFormDefinition(input: $input) {
      ok
      errors {
        field
        messages
      }
    }
  }
`;

export const PUBLISH_FORM = gql`
  mutation PublishForm($slug: String!) {
    publishForm(slug: $slug) {
      ok
      errors {
        field
        messages
      }
    }
  }
`;

export const ARCHIVE_FORM = gql`
  mutation ArchiveForm($slug: String!) {
    archiveForm(slug: $slug) {
      ok
      errors {
        field
        messages
      }
    }
  }
`;

export const SUBMIT_FORM = gql`
  mutation SubmitForm($slug: String!, $payload: JSON!) {
    submitForm(slug: $slug, payload: $payload) {
      ok
      submissionId
      errors {
        field
        messages
      }
    }
  }
`;

export const UPDATE_SUBMISSION_STATUS = gql`
  mutation UpdateSubmissionStatus($submissionId: ID!, $status: String!) {
    updateSubmissionStatus(submissionId: $submissionId, status: $status) {
      ok
      errors {
        field
        messages
      }
    }
  }
`;
