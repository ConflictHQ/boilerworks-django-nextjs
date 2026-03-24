import graphene

from .device_token import *
from .notification_config import *


class Mutation(graphene.ObjectType, NotificationConfigMutations):
    device_token = DeviceTokenMutation.Field()
    notification_config = NotificationConfigMutation.Field()
