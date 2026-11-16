import { gql } from "@apollo/client";

export const SUPERSET_GUEST_TOKEN = gql`
  mutation SupersetGuestToken($dashboard: ID!) {
    supersetGuestToken(dashboard: $dashboard) {
      ok
      token
      errors {
        field
        messages
      }
    }
  }
`;
