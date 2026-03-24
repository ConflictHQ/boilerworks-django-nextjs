import dataclasses
import inspect

import config.schema as ConfigSchema
from core.schema.context import StrawberryContext
from core.tests.utils.document_writer import DocWriter
from django.contrib.auth.models import Permission, User
from django.contrib.contenttypes.models import ContentType
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory
from organization.models import Organization, OrganizationMember
from snapshottest.django import TestCase


def add_session_to_request(request):
    middleware = SessionMiddleware(lambda x: None)
    middleware.process_request(request)
    request.session.save()


@dataclasses.dataclass
class QueryTest:
    query: str = None
    variables: dict = dataclasses.field(default_factory=dict)
    client: Client = dataclasses.field(
        default_factory=lambda: Client(ConfigSchema.schema, execution_context_class=DeferredExecutionContext)
    )
    factory: RequestFactory = dataclasses.field(default_factory=RequestFactory)
    user: User = dataclasses.field(default_factory=lambda: User.objects.get_or_create(username='testuser')[0])
    request = None
    response = None

    def __post_init__(self):
        request = self.factory.get('/')
        request.user = self.user
        add_session_to_request(request)
        self.request = DataLoaderContext(request=request)

    def add_variable(self, **kwargs):
        self.variables.update(kwargs)
        return self

    def introspection(self, gql_type: str):
        introspection_query = """
        {
          __type(name: "{gql_type}") {
            fields {
              name
              args {
                name
                type {
                  name
                  kind
                }
                defaultValue
              }
            }
          }
        }
        """.replace('{gql_type}', gql_type)
        introspection_result = self.client.execute(introspection_query, context_value=self.request)
        fields = [field["name"] for field in introspection_result["data"]["__type"]["fields"]]
        fields_string = " ".join(fields)
        self.query = f"""
            query {{
              allMyModels {{
                {fields_string}
              }}
            }}
        """
        return self

    def execute(self):
        self.response = self.client.execute(self.query, variables=self.variables, context_value=self.request)
        return self

    def assertQueryResult(self, test):
        self.response = self.response or self.execute().response
        test.assertEqual.__self__.maxDiff = None
        test.assertEqual(0, len(self.response.get('errors', ())), str(self.response))
        test.assertMatchSnapshot(self.response)
        DocWriter.write_to_doc(self._get_function(test), self.variables, self.query, self.response)

    def assertQueryError(self, test, mutation_name=None):
        if mutation_name:
            mutation_data = self.response.get('data', {}).get(mutation_name)
            if mutation_data is not None:
                test.assertTrue(0 < len(mutation_data), str(self.response))
            else:
                test.assertTrue(0 < len(self.response.get('errors', ())), str(self.response))
        else:
            test.assertTrue(0 < len(self.response.get('errors', ())), str(self.response))
        test.assertMatchSnapshot(self.response)
        DocWriter.write_to_doc(self._get_function(test), self.variables, self.query, self.response)

    def _get_function(self, test):
        for s in inspect.stack():
            if s.function.startswith('test_') and getattr(test, s.function, None):
                return getattr(test, s.function)

        raise Exception('No test function found')


class BaseTest(TestCase):

    def setUp(self):
        # settings.DEBUG = True
        self.client = Client(ConfigSchema.schema, execution_context_class=DeferredExecutionContext)
        self.factory = RequestFactory()
        self.user, _ = User.objects.get_or_create(username='testuser')
        self.user.is_superuser = True
        self.user.is_staff = True
        self.user.save()
        self.organization, _ = Organization.objects.get_or_create(name='Test Org', slug='test-org')
        OrganizationMember.objects.get_or_create(member=self.user, organization=self.organization)
        from core.models import Profile
        self.profile, _ = Profile.objects.get_or_create(user=self.user)
        self.profile.active_organization = self.organization
        self.profile.save()

    def request(self):
        request = self.factory.get('/')
        request.user = self.user
        add_session_to_request(request)
        context = DataLoaderContext(request=request)
        return context

    def get_function(self, index=2):
        for s in inspect.stack():
            if s.function.startswith('test_') and getattr(self, s.function, None):
                return getattr(self, s.function)

        raise Exception('No test function found')

    def create_permission(self, app_label, model, codename, name):

        content_type, _ = ContentType.objects.get_or_create(
            app_label=app_label,
            model=model
        )

        self.view_perm = Permission.objects.create(
            codename=codename,
            name=name,
            content_type=content_type
        )

    def assertQueryResult(self, query, variables, response):
        self.assertEqual.__self__.maxDiff = None
        self.assertEqual(0, len(response.get('errors', ())), str(response))
        self.assertMatchSnapshot(response)
        DocWriter.write_to_doc(self.get_function(3), variables, query, response)

    def assertQueryError(self, query, variables, response, mutation_name=None):
        if mutation_name:
            mutation_data = response.get('data', {}).get(mutation_name)
            if mutation_data is not None:
                self.assertTrue(0 < len(mutation_data), str(response))
            else:
                self.assertTrue(0 < len(response.get('errors', ())), str(response))
        else:
            self.assertTrue(0 < len(response.get('errors', ())), str(response))
        self.assertMatchSnapshot(response)
        DocWriter.write_to_doc(self.get_function(3), variables, query, response)

    def assertException(self, lambda_func, message=None):
        with self.assertRaises(Exception) as context:
            lambda_func()

        messages = [message] if isinstance(message, str) else message
        found = []
        for message in messages:
            if str(context.exception).find(message) >= 0:
                found.append(message)

        if len(found) != len(messages):
            if context.exception:
                raise context.exception
            raise Exception(f'Not Raise: {set(messages) - set(found)}')

        self.assertTrue(str(context.exception).find(message) >= 0, str(context.exception))
