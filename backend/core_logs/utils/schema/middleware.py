from core_logs.models import GQLLog


class LoggerMiddleware(object):

    def resolve(self, next, root, info, **args):
        error = None
        result = None
        try:
            result = next(root, info, **args)
        except Exception as e:
            error = e
            raise e
        finally:
            GQLLog.log(
                info=info,
                result=result,
                error=error,
            )

        return result
