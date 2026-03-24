import graphene

from .component import *


class Mutation(graphene.ObjectType):
    component = ComponentMutation.Field()
