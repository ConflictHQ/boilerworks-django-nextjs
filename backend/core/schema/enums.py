import graphene
from core.models import NotificationStatus, Profile

CoreProfileDocumentOptionChoices = graphene.Enum('CoreProfileDocumentOptionChoices', [
    (e.name, e.value) for e in list(Profile.DocumentOptions)
])

EnumNotificationStatus = graphene.Enum('EnumNotificationStatus', [
    (e.name, e.value) for e in list(NotificationStatus)
])()
