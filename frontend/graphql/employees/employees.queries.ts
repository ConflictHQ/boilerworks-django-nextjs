import { gql } from "@apollo/client";

export const getEmployees = gql`
  query Employees(
    $first: Int
    $offset: Int
    $search: String
    $showDeactivated: Boolean
    $departments_Department_Name_Icontains: String
    $departments_Position_Name_Icontains: String
  ) {
    employees(
      first: $first
      offset: $offset
      search: $search
      departments_Department_Name_Icontains: $departments_Department_Name_Icontains
      departments_Position_Name_Icontains: $departments_Position_Name_Icontains
      showDeactivated: $showDeactivated
    ) {
      totalCount
      edges {
        cursor
        node {
          id
          user {
            id
            firstName
            lastName
            profile {
              id
              displayName
              firstName
              lastName
              avatar {
                publicPermanentUrl
              }
            }
            email
            isActive
          }
        }
      }
      pageInfo {
        hasNextPage
      }
    }
  }
`;
