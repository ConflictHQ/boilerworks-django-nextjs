from core.tests.utils.base_test import BaseTest
from strawberry.relay import to_base64 as to_global_id


class UserTest(BaseTest):

    def test_get_current_user(self):
        """
        Returns the user information from the requesting session.
        :return:
        """
        request = self.request()

        query = '''
          query Me {
            me {
              username
              email
              firstName
              isActive
              lastName
            }
          }
        '''
        variables = {}
        response = self.client.execute(query, variables=variables, context_value=request)
        self.assertQueryResult(query, variables, response)

    def test_get_user_by_id(self):
        """user(id:) query returns the correct user when given a valid relay ID."""
        request = self.request()
        query = '''
          query User($id: ID!) {
            user(id: $id) {
              id
              username
            }
          }
        '''
        user_relay_id = to_global_id("UserType", self.user.pk)
        variables = {"id": user_relay_id}
        response = self.client.execute(query, variables=variables, context_value=request)

        self.assertEqual(0, len(response.get('errors', ())), str(response))
        self.assertEqual(response['data']['user']['username'], 'testuser')
        self.assertEqual(response['data']['user']['id'], user_relay_id)

    def test_get_users_filtered_by_search(self):
        """users(search:) query returns users whose username matches the search term."""
        request = self.request()
        query = '''
            query users($first: Int, $search: String) {
              users(first: $first, search: $search) {
                totalCount
                edges {
                  node {
                    username
                  }
                }
              }
            }
        '''
        variables = {'first': 5, 'search': 'testuser'}
        response = self.client.execute(query, variables=variables, context_value=request)

        self.assertEqual(0, len(response.get('errors', ())), str(response))
        usernames = [e['node']['username'] for e in response['data']['users']['edges']]
        self.assertIn('testuser', usernames)


class ProfileTest(BaseTest):

    def test_get_current_user_profile(self):
        """
        Returns the profile information from the requesting session.
        :return:
        """
        request = self.request()

        query = '''
        {
          me {
            profile {
              firstName
              lastName
              phoneNumber
              emergencyPhoneNumber
              emergencyContactName
              preferredContact
              address {
                street
                state
                zipcode
              }
            }
          }
        }

        '''
        variables = {}
        response = self.client.execute(query, variables=variables, context_value=request)
        self.assertQueryResult(query, variables, response)

    def test_upsert_current_user_profile(self):
        """
        Updates the profile information for the current user, with the given input.
        **Note** If there is no profile in the database, then it will be created
        even though this should happen when the User was added to the system.
        :return:
        """
        request = self.request()

        mutation = '''
        mutation {
          profile (
            input:{
              user : {
                      firstName:"Jesus"
                      lastName: "Doe"
              }
              displayName:"Jane Doe Smith"
              address: {
                      street:"Street6134213"
                      state:FL
                      city:"City"
                      zipcode:"12345-6789"
              }
          }
          ){
              ok
              errors {
                field
                messages
            }
          }
        }
        '''
        variables = {}
        response = self.client.execute(mutation, variables=variables, context_value=request)
        self.assertQueryResult(mutation, variables, response)

    def test_upsert_current_user_profile_fails_serialization(self):
        """
        Update fails because given profile information has formatting issues (i.e. invalid phone format)
        :return:
        """
        request = self.request()

        mutation = '''
        mutation {
          profile (
            input:{
              user : {
                      firstName:"Jesus"
                      lastName: "Doe"
              }
              phoneNumber:"1"
              emergencyPhoneNumber:"1"
              address: {
                      street:"Street6134213"
                      state:FL
                      city:"City"
                      zipcode:"12345-6789"
              }
          }
          ){
              ok
              errors {
                field
                messages
            }
          }
        }
        '''
        variables = {}
        response = self.client.execute(mutation, variables=variables, context_value=request)
        self.assertQueryError(mutation, variables, response, 'profile')

    def test_upsert_profile_for_given_user_fails_serialization(self):
        """
        Update fails because given profile information has formatting issues (i.e. invalid phone format)
        """
        request = self.request()

        mutation = '''
        mutation($userId:String!){
          profile (
            input:{
              user:{
                id:$userId
                email:"new_em"
              }
              displayName:"Jane Doe Smith"
              birthDate:"1995-11-18"
              gender:MALE
              phoneNumber:"+18"
              emergencyPhoneNumber:"+18"
              emergencyContactName:"Jane Doe Sr"
              preferredContact:SMS
              address: {
                      street:"Street 543"
                      state:FL
                      city:"City"
                      zipcode:"19999999999999999999980808080808"
              }
          }
          ){
              ok
              errors {
                field
                messages
            }
          }
        }
        '''
        variables = {'userId': 'VXNlclR5cGU6MQ=='}
        response = self.client.execute(mutation, variables=variables, context_value=request)
        self.assertQueryError(mutation, variables, response, 'profile')
