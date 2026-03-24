"""
Custom django-health-check backend for OpenSearch.

Registered in CoreConfig.ready() via plugin_dir.register().
"""
from health_check.backends import BaseHealthCheck
from health_check.exceptions import ServiceUnavailable


class OpenSearchHealthCheck(BaseHealthCheck):
    critical_service = True

    def check_status(self):
        try:
            from opensearch_dsl import connections
            conn = connections.get_connection()
            if not conn.ping():
                self.add_error(ServiceUnavailable("OpenSearch ping returned False"))
        except ServiceUnavailable:
            raise
        except Exception as e:
            self.add_error(ServiceUnavailable(str(e)))

    def identifier(self):
        return "OpenSearch"
