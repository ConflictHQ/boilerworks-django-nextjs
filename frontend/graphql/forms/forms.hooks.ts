import { useMutation, useQuery } from "@apollo/client/react";

import {
  CREATE_FORM_DEFINITION,
  PUBLISH_FORM,
  ARCHIVE_FORM,
  SUBMIT_FORM,
  UPDATE_SUBMISSION_STATUS,
} from "./forms.mutations";
import {
  GET_FORM_DEFINITION,
  GET_FORM_DEFINITIONS,
  GET_FORM_FIELD_TYPES,
  GET_FORM_SUBMISSIONS,
} from "./forms.queries";
import type {
  FormDefinitionData,
  FormDefinitionsData,
  FormFieldTypesData,
  FormSubmissionsData,
  MutationResultData,
  SubmitFormData,
} from "./forms.types";

export const useFormDefinitions = (status?: string) => {
  const { data, loading, error, refetch } = useQuery<FormDefinitionsData>(GET_FORM_DEFINITIONS, {
    variables: { status },
    fetchPolicy: "cache-and-network",
  });
  return { forms: data?.formDefinitions ?? [], loading, error, refetch };
};

export const useFormDefinition = (slug: string) => {
  const { data, loading, error } = useQuery<FormDefinitionData>(GET_FORM_DEFINITION, {
    variables: { slug },
    fetchPolicy: "cache-and-network",
    skip: !slug,
  });
  return { form: data?.formDefinition ?? null, loading, error };
};

export const useFormSubmissions = (slug: string, status?: string) => {
  const { data, loading, error, refetch } = useQuery<FormSubmissionsData>(GET_FORM_SUBMISSIONS, {
    variables: { slug, status },
    fetchPolicy: "cache-and-network",
    skip: !slug,
  });
  return { submissions: data?.formSubmissions ?? [], loading, error, refetch };
};

export const useFormFieldTypes = () => {
  const { data, loading } = useQuery<FormFieldTypesData>(GET_FORM_FIELD_TYPES, {
    fetchPolicy: "cache-first",
  });
  return { fieldTypes: data?.formFieldTypes ?? [], loading };
};

export const useCreateFormDefinition = () =>
  useMutation<MutationResultData>(CREATE_FORM_DEFINITION, {
    refetchQueries: [GET_FORM_DEFINITIONS],
  });

export const usePublishForm = () =>
  useMutation<MutationResultData>(PUBLISH_FORM, {
    refetchQueries: [GET_FORM_DEFINITIONS],
  });

export const useArchiveForm = () =>
  useMutation<MutationResultData>(ARCHIVE_FORM, {
    refetchQueries: [GET_FORM_DEFINITIONS],
  });

export const useSubmitForm = () =>
  useMutation<SubmitFormData>(SUBMIT_FORM);

export const useUpdateSubmissionStatus = () =>
  useMutation<MutationResultData>(UPDATE_SUBMISSION_STATUS);
