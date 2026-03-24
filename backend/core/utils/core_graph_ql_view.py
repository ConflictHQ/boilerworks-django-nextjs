import json
import logging
import time
from datetime import timedelta

from core.dataloaders import DataLoaderContext
from core.utils.performance import cache_class_method
from core_logs.models import GQLLog, PermissionAccessLog
from django.conf import settings
from graphene_file_upload.django import FileUploadGraphQLView
from graphql import ExecutionResult

logger = logging.getLogger(__name__)

to_cache = ('IntrospectionQuery',)


class CoreGraphQLView(FileUploadGraphQLView):
    def get_context(self, request):
        return DataLoaderContext(request)

    @staticmethod
    def _serializer_deserializer(store: bool, data):
        if store:
            return dict(
                data=json.dumps(data.data),
                errors=json.dumps(data.errors),
                extensions=json.dumps(data.extensions),
            )
        else:
            return ExecutionResult(
                data=json.loads(data['data']),
                errors=json.loads(data['errors']),
                extensions=json.loads(data['extensions']),
            )

    @staticmethod
    def _gen_key(*args, **kwargs):
        return f'query_{hash(args[3])}_vars_{hash(args[4])}'

    @cache_class_method(timeout=timedelta(minutes=10), key_gen=_gen_key, serializer=_serializer_deserializer)
    def _cache_execute_gql_request(self, request, data, query, variables, operation_name, *args, **kwargs):
        return super().execute_graphql_request(request, data, query, variables, operation_name, *args, **kwargs)

    # @silk_profile(name='execute_graphql_request')
    def _profile_execute_gql_request(self, request, data, query, variables, operation_name, *args, **kwargs):
        return super().execute_graphql_request(request, data, query, variables, operation_name, *args, **kwargs)

    def execute_graphql_request(self, request, data, query, variables, operation_name, *args, **kwargs):

        start = time.time()
        if operation_name in to_cache:
            execution_result = self._cache_execute_gql_request(request, data, query, variables, operation_name, *args,
                                                               **kwargs)
        else:
            execution_result = self._profile_execute_gql_request(request, data, query, variables, operation_name, *args,
                                                                 **kwargs)
        end = time.time()
        GQLLog.log(
            context=request,
            data=data,
            result=execution_result,
            errors=execution_result.errors,
            duration=timedelta(seconds=end - start),
            request_profiling=getattr(request, 'profiling', None),
        )

        PermissionAccessLog.flush()

        if execution_result and execution_result.errors:
            if settings.DEBUG:
                try:
                    dump = f'============================>>>\n{query}\n      Response ---------------------------------------\n'
                    if execution_result.errors:
                        if hasattr(request, 'django_debug'):
                            for e in request.django_debug.object.exceptions:
                                dump += f'    {e.stack}\n'
                    else:
                        dump += '    response ok\n'
                    dump += '<<<============================\n'
                    logger.warning(dump)
                except Exception as e:
                    logger.warning('request ', e)
        elif settings.DEBUG:
            if hasattr(request, "data"):
                logger.debug(request.data)
            elif hasattr(request, "POST"):
                logger.debug(request.POST)

        return execution_result
