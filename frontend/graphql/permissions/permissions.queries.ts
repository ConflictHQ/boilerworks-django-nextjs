import { gql } from "@apollo/client";

export const GET_PERMISSION = gql`
  query Permission($slug: String!) {
    component(slug: $slug) {
      isActive
    }
  }
`;
