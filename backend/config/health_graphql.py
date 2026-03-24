"""Health check for the Strawberry GraphQL endpoint."""
from health_check.backends import BaseHealthCheck
from health_check.exceptions import ServiceUnavailable


class GraphQLHealthCheck(BaseHealthCheck):
    critical_service = True

    def check_status(self):
        try:
            from config.schema import schema
            result = schema.execute_sync('{ __typename }')
            if result.errors:
                self.add_error(ServiceUnavailable(f'GraphQL errors: {result.errors}'))
            elif result.data.get('__typename') != 'Query':
                self.add_error(ServiceUnavailable('Unexpected __typename'))
        except Exception as e:
            self.add_error(ServiceUnavailable(f'GraphQL unavailable: {e}'))

    def identifier(self):
        return 'GraphQL (Strawberry)'
