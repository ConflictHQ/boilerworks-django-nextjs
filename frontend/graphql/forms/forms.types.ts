export type FormDefinition = {
  name: string;
  slug: string;
  description: string;
  status: string;
  version: number;
  schema: Record<string, unknown>;
  formType?: string;
  isPublic?: boolean;
  publishedAt: string | null;
  createdAt: string;
  updatedAt: string;
  submissionCount: number;
};

export type FormSubmission = {
  payload: Record<string, unknown>;
  status: string;
  submittedAt: string;
  createdAt: string;
  formName: string;
  formVersion: number;
  formSlug: string;
};

export type FormDefinitionsData = {
  formDefinitions: FormDefinition[];
};

export type FormDefinitionData = {
  formDefinition: FormDefinition | null;
};

export type FormSubmissionsData = {
  formSubmissions: FormSubmission[];
};

export type FormFieldTypesData = {
  formFieldTypes: string[];
};

export type SubmitFormData = {
  submitForm: {
    ok: boolean;
    submissionId: string | null;
    errors: { field: string; messages: string[] }[];
  };
};

export type MutationResultData = {
  [key: string]: {
    ok: boolean;
    errors: { field: string; messages: string[] }[];
  };
};
