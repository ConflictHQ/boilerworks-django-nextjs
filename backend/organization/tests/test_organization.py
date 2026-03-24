from core.tests.utils.base_test import BaseTest
from strawberry.relay import to_base64 as to_global_id


class OrganizationMemberTest(BaseTest):

    def test_organization_member_can_be_deactivated(self):
        """organizationMemberStatus mutation deactivates the requesting user in their own org."""
        request = self.request()

        mutation = '''
        mutation ($userId: String!, $isActive: Boolean!) {
          organizationMemberStatus(input: {userId: $userId, isActive: $isActive}) {
            ok
            errors {
              field
              messages
            }
          }
        }
        '''
        # Derive the relay ID dynamically — not coupled to any specific sequence value.
        user_relay_id = to_global_id("UserType", self.user.pk)
        variables = {"userId": user_relay_id, "isActive": False}
        response = self.client.execute(mutation, variables=variables, context_value=request)

        self.assertEqual(0, len(response.get('errors', ())), str(response))
        data = response['data']['organizationMemberStatus']
        self.assertTrue(data['ok'])
        self.assertEqual(data['errors'], [])

    def test_organization_member_status_unknown_user_returns_gql_error(self):
        """organizationMemberStatus mutation returns a GQL error when the userId doesn't belong to any member."""
        request = self.request()

        mutation = '''
        mutation ($userId: String!, $isActive: Boolean!) {
          organizationMemberStatus(input: {userId: $userId, isActive: $isActive}) {
            ok
            errors {
              field
              messages
            }
          }
        }
        '''
        # A relay ID that will never exist in the test database.
        variables = {"userId": to_global_id("UserType", 9_999_999), "isActive": False}
        response = self.client.execute(mutation, variables=variables, context_value=request)

        self.assertTrue(
            len(response.get('errors', ())) > 0
            or (response.get('data', {}).get('organizationMemberStatus') is None),
            f"Expected an error or null result, got: {response}",
        )
