"""Health check for the Strawberry GraphQL endpoint."""
from health_check.backends import BaseHealthCheckBackend
from health_check.exceptions import HealthCheckException


class GraphQLHealthCheck(BaseHealthCheckBackend):
    critical_service = True

    def check_status(self):
        try:
            from config.schema import schema
            result = schema.execute_sync('{ __typename }')
            if result.errors:
                raise HealthCheckException(f'GraphQL errors: {result.errors}')
            if result.data.get('__typename') != 'Query':
                raise HealthCheckException('GraphQL returned unexpected __typename')
        except Exception as e:
            raise HealthCheckException(f'GraphQL unavailable: {e}')

    def identifier(self):
        return 'GraphQL (Strawberry)'
