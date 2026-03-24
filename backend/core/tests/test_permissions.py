from core.tests.utils.base_test import BaseTest
from django.contrib.auth.models import Group, User


class PermissionsTest(BaseTest):
    def setUp(self):
        super().setUp()
        # Tests use hardcoded graphene global IDs: UserType:5, UserType:10, GroupType:4
        User.objects.get_or_create(pk=5, defaults={'username': 'test_user_5'})
        User.objects.get_or_create(pk=10, defaults={'username': 'test_user_10'})
        group, _ = Group.objects.get_or_create(pk=4, defaults={'name': 'TestGroup'})
        # Group must belong to the organization for GroupType.get_queryset to find it
        self.organization.groups.add(group)

    def test_get_permission_groups(self):
        """
        Returns the list of permission groups a user can be affiliated to.
        :return:
        """
        request = self.request()

        query = '''
          query Groups($id:ID) {
            groups(id:$id) {
              edges {
                node {
                    id
                    name
                  }
                }
              }
          }
        '''
        variables = {'id': None}
        response = self.client.execute(query, variables=variables, context_value=request)
        self.assertQueryResult(query, variables, response)

    def test_get_permission_group_filter_by_id(self):
        """
        Returns the permission group for the given id.
        :return:
        """
        request = self.request()

        query = '''
          query Groups($id:ID) {
            groups(id:$id) {
              edges {
                node {
                    id
                    name
                    userSet  {
                      edges {
                        node {
                          id
                          username
                          firstName
                          lastName
                        }
                      }
                    }
                  }
                }
              }
          }
        '''
        variables = {'id': 'R3JvdXBUeXBlOjQ='}
        response = self.client.execute(query, variables=variables, context_value=request)
        self.assertQueryResult(query, variables, response)

    def test_get_permission_group_filter_by_name(self):
        """
        Returns the permission groups which names are similar to the given string.
        :return:
        """
        request = self.request()

        query = '''
            query groups {
              groups(name:"Platform") {
                edges {
                  node {
                    id
                    name
                  }
                }
              }
            }
        '''
        variables = {'name': 'adm'}
        response = self.client.execute(query, variables=variables, context_value=request)
        self.assertQueryResult(query, variables, response)

    def test_get_permission_group_with_only_filtered_users_by_search(self):
        """
        Returns the permission groups alongside the users who match the provided search criteria.
        :return:
        """
        request = self.request()

        query = '''
            query groups($groupName: String, $userFirst: Int, $userSearch: String) {
              groups(name: $groupName) {
                edges {
                  node {
                    id
                    name
                    userSet(first: $userFirst, search: $userSearch) {
                      totalCount
                      edges {
                        node {
                          username
                        }
                      }
                    }
                  }
                }
              }
            }
        '''
        variables = {'groupName': None, 'userFirst': 3, 'userSearch': "testuser"}
        response = self.client.execute(query, variables=variables, context_value=request)
        self.assertQueryResult(query, variables, response)

    def test_add_user_to_permission_group(self):
        """
        Returns the list of permission groups a user can be affiliated to.
        :return:
        """
        request = self.request()

        query = '''
            mutation permissionGroupOperation(
                $userIds: [String]!
                $groupId: String!
                $operation: operation!
            ){
              permissionGroupOperation(
                input : {
                  userIds: $userIds
                  groupId: $groupId
                  operation: $operation
                }
              ) {
                ok
                errors {
                  messages
                }
              }
            }
        '''
        variables = {
            'userIds': ['VXNlclR5cGU6MTA=', 'VXNlclR5cGU6NQ=='],
            'groupId': 'R3JvdXBUeXBlOjQ=',
            'operation': 'ADD'
        }
        response = self.client.execute(query, variables=variables, context_value=request)
        self.assertQueryResult(query, variables, response)

    def test_remove_user_from_permission_group(self):
        """
        Returns the list of permission groups a user can be affiliated to.
        :return:
        """
        request = self.request()

        query = '''
            mutation permissionGroupOperation(
                $userIds: [String]!
                $groupId: String!
                $operation: operation!
            ){
              permissionGroupOperation(
                input : {
                  userIds: $userIds
                  groupId: $groupId
                  operation: $operation
                }
              ) {
                ok
                errors {
                  messages
                }
              }
            }
        '''
        variables = {
            'userIds': ['VXNlclR5cGU6MTA=', 'VXNlclR5cGU6NQ=='],
            'groupId': 'R3JvdXBUeXBlOjQ=',
            'operation': 'REMOVE'
        }
        response = self.client.execute(query, variables=variables, context_value=request)
        self.assertQueryResult(query, variables, response)
