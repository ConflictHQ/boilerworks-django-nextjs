import { gql } from "@apollo/client";

export const GET_SUPERSET_DASHBOARDS = gql`
  query GetSupersetDashboards {
    supersetDashboards {
      guid
      embeddedId
      title
      description
      order
      supersetDomain
    }
  }
`;
