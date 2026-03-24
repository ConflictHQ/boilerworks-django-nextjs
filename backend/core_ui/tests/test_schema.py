from core.tests.utils.base_test import BaseTest
from core_ui.models import Component


class ComponentTest(BaseTest):

    def setUp(self):
        super().setUp()
        # Tests use hardcoded global IDs: ComponentType:3, ComponentType:4, ComponentType:5
        # and filter by slug "dashboard"
        Component.objects.get_or_create(pk=3, defaults={'name': 'component3', 'path': '/c3', 'slug': 'component3'})
        Component.objects.get_or_create(pk=4, defaults={'name': 'dashboard', 'path': '/dashboard', 'slug': 'dashboard'})
        Component.objects.get_or_create(pk=5, defaults={'name': 'component5', 'path': '/c5', 'slug': 'component5'})

    def test_should_get_all_components(self):
        """
        ## Retrieve all ui components
            Permissions affect visibility, if you don't have access to
            a component it won't show on the query results
        """
        request = self.request()
        mutation = '''
            query Components {
              components {
                edges {
                  node {
                    name
                    id
                  }
                }
              }
            }
        '''
        variables = {}
        response = self.client.execute(mutation, variables=variables, context_value=request)
        self.assertQueryResult(mutation, variables, response)

    def test_should_filter_component_by_slug(self):
        """
        ## Filter component by slug

           Filter: *slug*: of the component to retrieved
        """
        request = self.request()

        mutation = '''
          query Components($slug: String!) {
            components(slug: $slug) {
              edges {
                node {
                  id
                  slug
                  components {
                    edges {
                      node {
                        slug
                        guid
                      }
                    }
                  }
                }
              }
            }
          }
        '''
        variables = {"slug": "dashboard"}
        response = self.client.execute(mutation, variables=variables, context_value=request)
        self.assertQueryResult(mutation, variables, response)

    def test_create_ui_component(self):
        """
        ## Create UI component mutation

           If ID is given, it will update the component, otherwise it will create a new one
        """
        request = self.request()
        mutation = '''
            mutation Component {
              component (input :{
                name: "my_component"
                path: "/my-component"
                slug: "mycomponent"
                description:"component for testing"
                properties: "{\\\"title\\\": \\\"Test Title\\\", \\\"description\\\": \\\"Test Description\\\"}"
                children : [
                  {
                    sortOrder:0,
                    childComponent:"Q29tcG9uZW50VHlwZTo0"
                  },
                  {
                    sortOrder:1,
                    childComponent: "Q29tcG9uZW50VHlwZToz"
                  }
                  {
                    sortOrder:2,
                    childComponent: "Q29tcG9uZW50VHlwZTo1"
                  }
                ]
              }){
                ok
                errors {
                  messages
                }
              }
            }
        '''
        variables = {}
        response = self.client.execute(mutation, variables=variables, context_value=request)
        self.assertQueryResult(mutation, variables, response)
        assert Component.objects.filter(slug="mycomponent").exists()

    def test_update_ui_component(self):
        """
        ## Update UI component mutation

           If ID is given, it will update the component, otherwise it will create a new one
        """
        request = self.request()
        mutation = '''
            mutation Component {
              component (input :{
                id: "Q29tcG9uZW50VHlwZTo0"
                name: "my_componentupdated"
                path: "/my-componentupdated"
                slug: "mycomponentupdated"
                description:"component for testing upadted"
                properties: "{\\\"title\\\": \\\"Test Title updated\\\", \\\"description\\\": \\\"Test Description\\\"}"
                children : [
                  {
                    sortOrder:0,
                    childComponent: "Q29tcG9uZW50VHlwZToz"
                  }
                  {
                    sortOrder:1,
                    childComponent: "Q29tcG9uZW50VHlwZTo1"
                  }
                ]
              }){
                ok
                errors {
                  messages
                }
              }
            }
        '''
        variables = {}
        response = self.client.execute(mutation, variables=variables, context_value=request)
        self.assertQueryResult(mutation, variables, response)
        assert Component.objects.filter(slug="mycomponentupdated").exists()

    def test_update_ui_component_invalid_order_sequence(self):
        """
        ## Update UI component fails due to invalid order sequence
            Provided sorting order for components must be a positive numeric
            sequence starting from zero and increasing by 1

        """
        request = self.request()
        mutation = '''
            mutation Component {
              component (input :{
                id: "Q29tcG9uZW50VHlwZTo0"
                name: "my_componentupdated"
                path: "/my-componentupdated"
                slug: "mycomponentupdated"
                description:"component for testing upadted"
                properties: "{\\\"title\\\": \\\"Test Title updated\\\", \\\"description\\\": \\\"Test Description\\\"}"
                children : [
                  {
                    sortOrder:0,
                    childComponent: "Q29tcG9uZW50VHlwZToz"
                  }
                  {
                    sortOrder:99,
                    childComponent: "Q29tcG9uZW50VHlwZTo1"
                  }
                ]
              }){
                ok
                errors {
                  messages
                }
              }
            }
        '''
        variables = {}
        response = self.client.execute(mutation, variables=variables, context_value=request)
        self.assertQueryError(mutation, variables, response)

    def test_update_ui_component_id_does_not_exist(self):
        """
        ## Update UI component fails due to not found id
           When an id is given, but not found, a graphqlError is raised

        """
        request = self.request()
        mutation = '''
            mutation Component {
              component (input :{
                id: "Q29tcG9uZW50VHlwZTo1OQ=="
                name: "my_componentupdated"
                path: "/my-componentupdated"
                slug: "mycomponentupdated"
                description:"component for testing upadted"
                properties: "{\\\"title\\\": \\\"Test Title updated\\\", \\\"description\\\": \\\"Test Description\\\"}"
                children : [
                  {
                    sortOrder:0,
                    childComponent: "Q29tcG9uZW50VHlwZToz"
                  }
                  {
                    sortOrder:1,
                    childComponent: "Q29tcG9uZW50VHlwZTo1"
                  }
                ]
              }){
                ok
                errors {
                  messages
                }
              }
            }
        '''
        variables = {}
        response = self.client.execute(mutation, variables=variables, context_value=request)
        self.assertQueryError(mutation, variables, response)
