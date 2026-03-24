from .mutations import *  # noqa
from .queries import *  # noqa
from .types import *  # noqa

schema = graphene.Schema(query=Query, mutation=Mutation)
